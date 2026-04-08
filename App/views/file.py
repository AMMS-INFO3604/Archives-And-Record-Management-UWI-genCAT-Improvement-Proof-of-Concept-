from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_jwt_extended import current_user as jwt_current_user
from flask_jwt_extended import jwt_required

from App.controllers.file import (
    addFile,
    changeFileStatus,
    deleteFile,
    getAllFiles,
    searchFile,
    updateFile,
    viewFile,
)
from App.controllers.patron import get_all_patrons
from App.database import db
from App.models import File

from App.controllers.box import getAllBoxes

from .index import index_views

file_views = Blueprint("file_views", __name__, template_folder="templates")

@file_views.route("/files/create", methods=["POST"])
@jwt_required()
def add_file_page():
    """Handle the Add File form submitted from the files page modal."""
    box_id       = request.form.get("boxID", "").strip()
    file_type    = request.form.get("fileType", "").strip()
    description  = request.form.get("description", "").strip() or None
    prev_desig   = request.form.get("previousDesignation", "").strip() or None
    date_created = request.form.get("dateCreated", "").strip() or None
    barcode      = request.form.get("barcode", "").strip() or None
 
    if not box_id or not file_type:
        flash("Box and file type are required.", "error")
        return redirect(url_for("file_views.get_files_page"))
 
    try:
        box_id = int(box_id)
    except ValueError:
        flash("Invalid box ID.", "error")
        return redirect(url_for("file_views.get_files_page"))
 
    file = addFile(
        boxID=box_id,
        fileType=file_type,
        description=description,
        previousDesignation=prev_desig,
        dateCreated=date_created,
        barcode=barcode,
        createdByStaffUserID=getattr(jwt_current_user, "id", None),
    )
 
    if file:
        flash(f"File #{file.fileID} created successfully.", "success")
    else:
        flash("Failed to create file. Please check your inputs.", "error")
 
    return redirect(url_for("file_views.get_files_page"))

@file_views.route("/api/files/batch", methods=["POST"])
@jwt_required()
def add_files_batch():
    """Handle batch file addition via API."""
    data = request.json
    if not data or "files" not in data:
        return jsonify({"error": "No data provided"}), 400
    
    files_to_add = data["files"]
    added_files = []
    
    try:
        for f_data in files_to_add:
            box_id = f_data.get("boxID")
            file_type = f_data.get("fileType")
            
            if not box_id or not file_type:
                continue
                
            file = addFile(
                boxID=int(box_id),
                fileType=file_type,
                description=f_data.get("description"),
                previousDesignation=f_data.get("previousDesignation"),
                barcode=f_data.get("barcode"),
                createdByStaffUserID=getattr(jwt_current_user, "id", None),
                commit=False
            )
            if file:
                added_files.append(file.fileID)
        
        db.session.commit()
        return jsonify({
            "message": f"Successfully added {len(added_files)} files.",
            "fileIDs": added_files
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
 

@file_views.route("/files", methods=["POST"])
@jwt_required()
def add_file():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    file = addFile(
        boxID=data.get("boxID"),
        fileType=data.get("fileType"),
        locationID=data.get("locationID"),
        loanID=data.get("loanID"),
        description=data.get("description"),
        previousDesignation=data.get("previousDesignation"),
        createdByStaffUserID=data.get("createdByStaffUserID"),
        dateCreated=data.get("dateCreated"),
    )
    if not file:
        return jsonify({"error": "Failed to add file"}), 400
    return jsonify({"message": "File added successfully", "fileID": file.fileID}), 201


@file_views.route("/files/<int:fileID>", methods=["PUT"])
@jwt_required()
def update_file(fileID):
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    file = updateFile(
        fileID=data.get("fileID") or fileID,
        boxID=data.get("boxID"),
        locationID=data.get("locationID"),
        loanID=data.get("loanID"),
        fileType=data.get("fileType"),
        description=data.get("description"),
        previousDesignation=data.get("previousDesignation"),
        createdByStaffUserID=data.get("createdByStaffUserID"),
        dateCreated=data.get("dateCreated"),
        status=data.get("status"),
        barcode=data.get("barcode"),
    )
    if not file:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"message": "File updated successfully", "fileID": file.fileID}), 200

@file_views.route("/files/<int:fileID>/delete", methods=["POST"])
@jwt_required()
def delete_file_page(fileID):
    result = deleteFile(fileID)
    if not result:
        flash(f"File {fileID} could not be deleted.", "error")
        return redirect(url_for("file_views.file_detail_page", fileID=fileID))
    flash(f"File #{fileID} was deleted successfully.", "success")
    return redirect(url_for("file_views.get_files_page"))


@file_views.route("/files/<int:fileID>", methods=["DELETE"])
@jwt_required()
def delete_file(fileID):
    result = deleteFile(fileID)

    if not result:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"message": f"File {fileID} was deleted successfully"}), 200


@file_views.route("/files/<int:fileID>", methods=["GET"])
@jwt_required()
def view_file(fileID):
    file = viewFile(fileID)

    if not file:
        return jsonify({"error": "File not found"}), 404

    return jsonify(
        {
            "fileID": file.fileID,
            "boxID": file.boxID,
            "locationID": file.locationID,
            "loanID": file.loanID,
            "fileType": file.fileType,
            "description": file.description,
            "previousDesignation": file.previousDesignation,
            "createdByStaffUserID": file.createdByStaffUserID,
            "dateCreated": str(file.dateCreated),
            "status": file.status,
            "barcode": file.barcode,
        }
    ), 200


@file_views.route("/files/<int:fileID>/detail", methods=["GET"])
@jwt_required()
def file_detail_page(fileID):
    file = viewFile(fileID)
    if not file:
        flash(f"File {fileID} not found.", "error")
        return redirect(url_for("file_views.get_files_page"))
    patrons = get_all_patrons()
    print("Patrons found:", len(patrons))
    return render_template("file_detail.html", file=file, patrons=patrons)


@file_views.route("/files", methods=["GET"])
@jwt_required()
def get_files_page():
    keyword = request.args.get("keyword", "").strip() or None
    fileType = request.args.get("fileType", "").strip() or None
    status = request.args.get("status", "").strip() or None
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to",   "").strip() or None
    page      = request.args.get("page", 1, type=int)
    files = searchFile(
        keyword=keyword,
        fileType=fileType,
        status=status,
        date_from=date_from,
        date_to=date_to,)
    
    per_page = 10                           
    total = len(files)
    start = (page - 1) * per_page
    paginated_files = files[start:start + per_page]

    total_pages = max(1, (total + per_page - 1) // per_page)

    boxes = getAllBoxes()
    
    return render_template(
        "files.html",
        files= paginated_files,
        boxes=boxes,
        keyword=keyword or "",
        fileType=fileType or "",
        status=status or "",
        date_from     = date_from or "",
        date_to       = date_to or "",
        page          = page,
        total_pages   = total_pages,
        total_results = total,
    )


@file_views.route("/api/files", methods=["GET"])
@jwt_required()
def get_all_files():
    files = getAllFiles()
    if not files:
        return jsonify({"message": "No files found"}), 404
    return jsonify(
        [
            {
                "fileID": f.fileID,
                "boxID": f.boxID,
                "fileType": f.fileType,
                "description": f.description,
                "status": f.status,
                "dateCreated": str(f.dateCreated),
            }
            for f in files
        ]
    ), 200


@file_views.route("/api/files/search", methods=["GET"])
@jwt_required()
def search_file():
    fileID = request.args.get("fileID")
    fileType = request.args.get("fileType")
    locationID = request.args.get("locationID")
    loanID = request.args.get("loanID")
    status = request.args.get("status")
    keyword = request.args.get("keyword")

    files = searchFile(
        fileID=fileID,
        fileType=fileType,
        locationID=locationID,
        loanID=loanID,
        status=status,
        keyword=keyword,
    )
    if not files:
        return jsonify({"message": "No files found"}), 404
    return jsonify(
        [
            {
                "fileID": f.fileID,
                "fileType": f.fileType,
                "status": f.status,
                "description": f.description,
                "locationID": f.locationID,
            }
            for f in files
        ]
    ), 200


@file_views.route("/files/<int:fileID>/status", methods=["PUT"])
@jwt_required()
def change_file_status(fileID):
    data = request.json
    if not data or "status" not in data:
        return jsonify({"error": "Status is required"}), 400

    file = changeFileStatus(fileID, data["status"])

    if not file:
        return jsonify({"error": "File not found or invalid status"}), 404
    return jsonify(
        {"message": f"File {fileID} status updated successfully", "status": file.status}
    ), 200