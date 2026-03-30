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

from datetime import date as _date
from App.controllers.location import get_all_locations
 
 
# ── Single File ───────────────────────────────────────────────────────────────
 
@file_views.route("/files/create/single-file/<file_type>", methods=["GET"])
@jwt_required()
def create_single_file_page(file_type):
    """Render the single-file creation form."""
    file_type = file_type.capitalize()
    boxes     = getAllBoxes()
    return render_template(
        "create_single_file.html",
        file_type = file_type,
        boxes     = boxes,
        today     = _date.today().isoformat(),
    )
 
 
@file_views.route("/files/create/single-file/<file_type>", methods=["POST"])
@jwt_required()
def create_single_file_action(file_type):
    """Handle single-file form submission."""
    file_type = file_type.capitalize()
    form      = request.form
 
    box_id      = form.get("boxID",            "").strip()
    description = form.get("description",      "").strip() or None
    prev_desig  = form.get("previousDesignation","").strip() or None
    date_created= form.get("dateCreated",      "").strip() or None
    barcode     = form.get("barcode",          "").strip() or None
 
    if not box_id:
        flash("Box is required.", "error")
        return redirect(request.url)
 
    try:
        box_id = int(box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)
 
    # Create the core file
    from App.controllers.file import addFile
    file = addFile(
        boxID                = box_id,
        fileType             = file_type,
        description          = description,
        previousDesignation  = prev_desig,
        dateCreated          = date_created,
        barcode              = barcode,
        createdByStaffUserID = getattr(jwt_current_user, "staffUserID", None),
    )
 
    if not file:
        flash("Failed to create file record.", "error")
        return redirect(request.url)
 
    # Create sub-record
    if file_type == "Student":
        from App.controllers.fileRecord import create_student_record
        create_student_record(
            fileID              = file.fileID,
            code                = form.get("studentCode", "").strip() or None,
            certificateDiploma  = form.get("certificateDiploma", "").strip() or None,
        )
    elif file_type == "Staff":
        from App.controllers.fileRecord import create_staff_record
        create_staff_record(
            fileID           = file.fileID,
            fileNumber       = form.get("fileNumber",       "").strip() or None,
            fileTitle        = form.get("fileTitle",        "").strip() or None,
            post             = form.get("post",             "").strip() or None,
            organisationUnit = form.get("organisationUnit", "").strip() or None,
            notes            = form.get("notes",            "").strip() or None,
        )
 
    flash(f"File #{file.fileID} created successfully.", "success")
    return redirect(url_for("file_views.file_detail_page", fileID=file.fileID))
 
 
# ── Single Part ───────────────────────────────────────────────────────────────
 
@file_views.route("/files/create/single-part/<file_type>", methods=["GET"])
@jwt_required()
def create_single_part_page(file_type):
    """Render the single-part creation form."""
    file_type    = file_type.capitalize()
    boxes        = getAllBoxes()
    locations    = get_all_locations()
    # Parent files = files of the same type that can receive parts
    from App.controllers.file import searchFile
    parent_files = searchFile(fileType=file_type)
    return render_template(
        "create_single_part.html",
        file_type    = file_type,
        boxes        = boxes,
        locations    = locations,
        parent_files = parent_files,
    )
 
 
@file_views.route("/files/create/single-part/<file_type>", methods=["POST"])
@jwt_required()
def create_single_part_action(file_type):
    """Handle single-part form submission."""
    file_type = file_type.capitalize()
    form      = request.form
 
    box_id        = form.get("boxID",         "").strip()
    location_id   = form.get("locationID",    "").strip() or None
    barcode       = form.get("barcode",       "").strip() or None
    volume_number = form.get("volumeNumber",  "").strip() or None
    start_date    = form.get("startDate",     "").strip() or None
    end_date      = form.get("endDate",       "").strip() or None
 
    if not box_id:
        flash("Box is required.", "error")
        return redirect(request.url)
 
    try:
        box_id = int(box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)
 
    from App.controllers.file import addFile
    file = addFile(
        boxID                = box_id,
        locationID           = int(location_id) if location_id else None,
        fileType             = file_type,
        barcode              = barcode,
        createdByStaffUserID = getattr(jwt_current_user, "staffUserID", None),
    )
 
    if not file:
        flash("Failed to create part record.", "error")
        return redirect(request.url)
 
    flash(f"Part #{file.fileID} created successfully.", "success")
    return redirect(url_for("file_views.file_detail_page", fileID=file.fileID))
 
 
# ── Batch File ────────────────────────────────────────────────────────────────
 
@file_views.route("/files/create/batch-file/<file_type>", methods=["GET"])
@jwt_required()
def create_batch_file_page(file_type):
    """Render the batch-file creation form."""
    file_type = file_type.capitalize()
    boxes     = getAllBoxes()
    return render_template(
        "create_batch_file.html",
        file_type = file_type,
        boxes     = boxes,
    )
 
 
@file_views.route("/files/create/batch-file/<file_type>", methods=["POST"])
@jwt_required()
def create_batch_file_action(file_type):
    """Handle batch-file form submission — saves every non-empty row."""
    file_type = file_type.capitalize()
    form      = request.form
 
    global_box_id     = form.get("globalBoxID",      "").strip()
    global_date       = form.get("globalDateCreated", "").strip() or None
 
    if not global_box_id:
        flash("Box selection is required.", "error")
        return redirect(request.url)
 
    try:
        global_box_id = int(global_box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)
 
    # Collect row lists
    descriptions   = form.getlist("row_description[]")
    prev_desigs    = form.getlist("row_prevDesig[]")
    codes          = form.getlist("row_code[]")
    cert_diplomas  = form.getlist("row_certDiploma[]")
    student_ids    = form.getlist("row_studentID[]")
    file_numbers   = form.getlist("row_fileNumber[]")
    file_titles    = form.getlist("row_fileTitle[]")  # staff title col
    staff_titles   = form.getlist("row_staffTitle[]") # staff-only title col
    posts          = form.getlist("row_post[]")
    org_units      = form.getlist("row_orgUnit[]")
 
    from App.controllers.file import addFile
    from App.controllers.fileRecord import create_student_record, create_staff_record
 
    created = 0
    errors  = 0
 
    for idx, desc in enumerate(descriptions):
        desc = desc.strip()
        pd   = prev_desigs[idx].strip() if idx < len(prev_desigs) else ""
        if not desc and not pd:
            continue  # skip empty rows
 
        file = addFile(
            boxID               = global_box_id,
            fileType            = file_type,
            description         = desc or None,
            previousDesignation = pd or None,
            dateCreated         = global_date,
            createdByStaffUserID= getattr(jwt_current_user, "staffUserID", None),
        )
 
        if not file:
            errors += 1
            continue
 
        if file_type == "Student":
            create_student_record(
                fileID             = file.fileID,
                code               = codes[idx].strip()         if idx < len(codes)         else None,
                certificateDiploma = cert_diplomas[idx].strip() if idx < len(cert_diplomas) else None,
            )
        elif file_type == "Staff":
            fn = file_numbers[idx].strip() if idx < len(file_numbers) else ""
            ft = (staff_titles[idx].strip() if idx < len(staff_titles) else "") or \
                 (file_titles[idx].strip()   if idx < len(file_titles)  else "")
            create_staff_record(
                fileID           = file.fileID,
                fileNumber       = fn or None,
                fileTitle        = ft or None,
                post             = posts[idx].strip()     if idx < len(posts)     else None,
                organisationUnit = org_units[idx].strip() if idx < len(org_units) else None,
            )
        created += 1
 
    if errors:
        flash(f"{created} record(s) created; {errors} failed.", "warning")
    else:
        flash(f"{created} record(s) created successfully.", "success")
 
    return redirect(url_for("file_views.get_files_page"))
 
 
# ── Batch Part ────────────────────────────────────────────────────────────────
 
@file_views.route("/files/create/batch-part/<file_type>", methods=["GET"])
@jwt_required()
def create_batch_part_page(file_type):
    """Render the batch-part creation form."""
    file_type    = file_type.capitalize()
    boxes        = getAllBoxes()
    locations    = get_all_locations()
    from App.controllers.file import searchFile
    parent_files = searchFile(fileType=file_type)
    return render_template(
        "create_batch_part.html",
        file_type    = file_type,
        boxes        = boxes,
        locations    = locations,
        parent_files = parent_files,
    )
 
 
@file_views.route("/files/create/batch-part/<file_type>", methods=["POST"])
@jwt_required()
def create_batch_part_action(file_type):
    """Handle batch-part form submission."""
    file_type = file_type.capitalize()
    form      = request.form
 
    global_box_id   = form.get("globalBoxID",      "").strip()
    global_loc_id   = form.get("globalLocationID", "").strip() or None
 
    if not global_box_id:
        flash("Box selection is required.", "error")
        return redirect(request.url)
 
    try:
        global_box_id = int(global_box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)
 
    file_ids    = form.getlist("row_fileID[]")
    volume_nos  = form.getlist("row_volumeNo[]")
    start_dates = form.getlist("row_startDate[]")
    end_dates   = form.getlist("row_endDate[]")
    barcodes    = form.getlist("row_barcode[]")
 
    from App.controllers.file import addFile
 
    created = 0
    errors  = 0
 
    for idx, fid in enumerate(file_ids):
        fid = fid.strip()
        if not fid:
            continue  # skip unselected rows
 
        file = addFile(
            boxID                = global_box_id,
            locationID           = int(global_loc_id) if global_loc_id else None,
            fileType             = file_type,
            barcode              = barcodes[idx].strip()    if idx < len(barcodes)    else None,
            createdByStaffUserID = getattr(jwt_current_user, "staffUserID", None),
        )
 
        if not file:
            errors += 1
            continue
        created += 1
 
    if errors:
        flash(f"{created} part(s) created; {errors} failed.", "warning")
    else:
        flash(f"{created} part(s) created successfully.", "success")
 
    return redirect(url_for("file_views.get_files_page"))

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