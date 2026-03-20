from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
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
from App.controllers.box import getAllBoxes
from App.controllers.location import get_all_locations
from App.controllers.patron import get_all_patrons

file_views = Blueprint("file_views", __name__, template_folder="templates")

@file_views.route("/files", methods=["GET"])
@jwt_required()
def get_files_page():
    search_query = request.args.get("search", "").strip() or None
    fileType = request.args.get("fileType", "").strip() or None
    status = request.args.get("status", "").strip() or None
    location_name = request.args.get("location", "").strip() or None

    all_locations_objs = get_all_locations()
    all_locations = [f"{loc.geoLocation}, {loc.campus}" for loc in all_locations_objs]

    # Get files based on basic filters
    files = searchFile(keyword=search_query, fileType=fileType, status=status)
    
    # Filter by location if specified
    if location_name and location_name != "all":
        parts = location_name.split(', ')
        geo = parts[0]
        camp = parts[1] if len(parts) > 1 else None
        files = [f for f in files if f.box and f.box.location and f.box.location.geoLocation == geo and (not camp or f.box.location.campus == camp)]

    boxes = getAllBoxes()
    return render_template(
        "files.html",
        files=files,
        boxes=boxes,
        locations=all_locations,
        search_query=search_query or "",
        fileType=fileType or "",
        status=status or "",
        selected_location=location_name or "all"
    )

@file_views.route("/files/<string:file_id>/detail", methods=["GET"])
@jwt_required()
def get_file_details_page(file_id):
    # Some IDs might be strings like 'STU-123', need to handle that
    # The viewFile controller might expect an ID or barcode
    file = viewFile(file_id)
    if not file:
        flash(f"File {file_id} not found.", "error")
        return redirect(url_for("file_views.get_files_page"))
    
    boxes = getAllBoxes()
    # Find active loan if any
    active_loan = next((l for l in (file.loans or []) if l.status == 'Active'), None)
    
    return render_template("file_detail.html", file=file, boxes=boxes, active_loan=active_loan)

@file_views.route("/files/create", methods=["POST"])
@jwt_required()
def create_file_action():
    fileID = request.form.get("fileID")
    description = request.form.get("description")
    fileType = request.form.get("fileType")
    boxID = request.form.get("boxID")

    if not all([fileID, description, fileType, boxID]):
        flash("All fields are required.", "error")
        return redirect(request.referrer or url_for("file_views.get_files_page"))

    # Mapping description
    file = addFile(
        boxID=boxID,
        fileType=fileType,
        description=description,
        barcode=fileID # Using fileID as barcode for scanner
    )
    
    if file:
        flash(f"File {fileID} created successfully.", "success")
    else:
        flash("Failed to create file.", "error")
        
    return redirect(request.referrer or url_for("file_views.get_files_page"))

@file_views.route("/files/<string:file_id>/edit", methods=["POST"])
@jwt_required()
def edit_file_action(file_id):
    description = request.form.get("description")
    fileType = request.form.get("fileType")
    boxID = request.form.get("boxID")

    file = updateFile(
        fileID=file_id,
        boxID=boxID,
        fileType=fileType,
        description=description
    )
    
    if file:
        flash(f"File {file_id} updated successfully.", "success")
    else:
        flash("Failed to update file.", "error")
        
    return redirect(url_for("file_views.get_file_details_page", file_id=file_id))

@file_views.route("/files/<string:file_id>/delete", methods=["POST"])
@jwt_required()
def delete_file_action(file_id):
    result = deleteFile(file_id)
    if result:
        flash(f"File {file_id} deleted successfully.", "success")
        return redirect(url_for("file_views.get_files_page"))
    else:
        flash(f"Failed to delete file {file_id}.", "error")
        return redirect(request.referrer or url_for("file_views.get_files_page"))

# API routes (rest unchanged or updated if needed)
# ...
