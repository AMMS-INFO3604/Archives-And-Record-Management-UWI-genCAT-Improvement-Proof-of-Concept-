from datetime import date as _date

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
from App.controllers.fileRecord import (
    create_staff_record,
    create_student_record,
    update_student_record,
    update_staff_record,
    get_student_record_by_file,
    get_staff_record_by_file,
)
from App.controllers.location import get_all_locations
from App.controllers.patron import get_all_patrons
from App.controllers.staffUser import get_staff_user_by_user
from App.controllers.box import getAllBoxes
from App.database import db
from App.models import File

file_views = Blueprint("file_views", __name__, template_folder="templates")


# ─────────────────────────────────────────────────────────────────────────────
# Helper – resolve the StaffUser ID for the currently logged-in user
# ─────────────────────────────────────────────────────────────────────────────

def _current_staff_id():
    """Return the staffUserID for the logged-in user, or None if not staff."""
    su = get_staff_user_by_user(jwt_current_user.userID)
    return su.staffUserID if su else None


# ─────────────────────────────────────────────────────────────────────────────
# File Edit page (GET + POST)
# ─────────────────────────────────────────────────────────────────────────────

@file_views.route("/files/<int:fileID>/edit", methods=["GET"])
@jwt_required()
def edit_file_page(fileID):
    file = viewFile(fileID)
    if not file:
        flash(f"File {fileID} not found.", "error")
        return redirect(url_for("file_views.get_files_page"))
    boxes = getAllBoxes()
    return render_template("file_edit.html", file=file, boxes=boxes, today=_date.today().isoformat())


@file_views.route("/files/<int:fileID>/edit", methods=["POST"])
@jwt_required()
def edit_file_action(fileID):
    """Handle the edit file form POST."""
    file = viewFile(fileID)
    if not file:
        flash(f"File {fileID} not found.", "error")
        return redirect(url_for("file_views.get_files_page"))

    form = request.form

    box_id_raw = form.get("boxID", "").strip()
    file_type = form.get("fileType", "").strip() or None
    description = form.get("description", "").strip() or None
    prev_desig = form.get("previousDesignation", "").strip() or None
    date_created = form.get("dateCreated", "").strip() or None
    status = form.get("status", "").strip() or None
    barcode = form.get("barcode", "").strip() or None

    box_id = None
    if box_id_raw:
        try:
            box_id = int(box_id_raw)
        except ValueError:
            flash("Invalid box selection.", "error")
            return redirect(url_for("file_views.edit_file_page", fileID=fileID))

    updated = updateFile(
        fileID=fileID,
        boxID=box_id,
        fileType=file_type,
        description=description,
        previousDesignation=prev_desig,
        dateCreated=date_created,
        status=status,
        barcode=barcode if barcode else None,
    )

    if not updated:
        flash("Failed to update the file record.", "error")
        return redirect(url_for("file_views.edit_file_page", fileID=fileID))

    # Update the type-specific sub-record
    if file_type == "Student" or (not file_type and file.fileType == "Student"):
        student_record = get_student_record_by_file(fileID)
        student_code = form.get("studentCode", "").strip() or None
        cert_diploma = form.get("certificateDiploma", "").strip() or None
        if student_record:
            update_student_record(
                studentID=student_record.studentID,
                code=student_code,
                certificateDiploma=cert_diploma,
            )
        else:
            create_student_record(fileID=fileID, code=student_code, certificateDiploma=cert_diploma)

    elif file_type == "Staff" or (not file_type and file.fileType == "Staff"):
        staff_record = get_staff_record_by_file(fileID)
        file_number = form.get("fileNumber", "").strip() or None
        file_title = form.get("fileTitle", "").strip() or None
        post = form.get("post", "").strip() or None
        org_unit = form.get("organisationUnit", "").strip() or None
        notes = form.get("notes", "").strip() or None
        if staff_record:
            update_staff_record(
                staffRecordID=staff_record.staffRecordID,
                fileNumber=file_number,
                fileTitle=file_title,
                post=post,
                organisationUnit=org_unit,
                notes=notes,
            )
        else:
            create_staff_record(
                fileID=fileID,
                fileNumber=file_number,
                fileTitle=file_title,
                post=post,
                organisationUnit=org_unit,
                notes=notes,
            )

    flash(f"File #{fileID} updated successfully.", "success")
    return redirect(url_for("file_views.file_detail_page", fileID=fileID))


# ─────────────────────────────────────────────────────────────────────────────
# CREATE FLOWS
# ─────────────────────────────────────────────────────────────────────────────

@file_views.route("/files/create/single-file/<file_type>", methods=["GET"])
@jwt_required()
def create_single_file_page(file_type):
    file_type = file_type.capitalize()
    return render_template(
        "single_file.html",
        file_type=file_type,
        boxes=getAllBoxes(),
        today=_date.today().isoformat(),
    )


@file_views.route("/files/create/single-file/<file_type>", methods=["POST"])
@jwt_required()
def create_single_file_action(file_type):
    file_type = file_type.capitalize()
    form = request.form

    box_id = form.get("boxID", "").strip()
    description = form.get("description", "").strip() or None
    prev_desig = form.get("previousDesignation", "").strip() or None
    date_created = form.get("dateCreated", "").strip() or None
    barcode = form.get("barcode", "").strip() or None

    if not box_id:
        flash("A box must be selected.", "error")
        return redirect(request.url)

    try:
        box_id = int(box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)

    file = addFile(
        boxID=box_id,
        fileType=file_type,
        description=description,
        previousDesignation=prev_desig,
        dateCreated=date_created,
        barcode=barcode,
        createdByStaffUserID=_current_staff_id(),
    )

    if not file:
        flash("Failed to create the file record. Please check your inputs.", "error")
        return redirect(request.url)

    if file_type == "Student":
        create_student_record(
            fileID=file.fileID,
            code=form.get("studentCode", "").strip() or None,
            certificateDiploma=form.get("certificateDiploma", "").strip() or None,
        )
    elif file_type == "Staff":
        create_staff_record(
            fileID=file.fileID,
            fileNumber=form.get("fileNumber", "").strip() or None,
            fileTitle=form.get("fileTitle", "").strip() or None,
            post=form.get("post", "").strip() or None,
            organisationUnit=form.get("organisationUnit", "").strip() or None,
            notes=form.get("notes", "").strip() or None,
        )

    flash(f"File #{file.fileID} created successfully.", "success")
    return redirect(url_for("file_views.file_detail_page", fileID=file.fileID))


@file_views.route("/files/create/single-part/<file_type>", methods=["GET"])
@jwt_required()
def create_single_part_page(file_type):
    file_type = file_type.capitalize()
    return render_template(
        "single_part.html",
        file_type=file_type,
        boxes=getAllBoxes(),
        locations=get_all_locations(),
        parent_files=searchFile(fileType=file_type) or [],
    )


@file_views.route("/files/create/single-part/<file_type>", methods=["POST"])
@jwt_required()
def create_single_part_action(file_type):
    file_type = file_type.capitalize()
    form = request.form

    box_id = form.get("boxID", "").strip()
    location_id = form.get("locationID", "").strip() or None
    barcode = form.get("barcode", "").strip() or None

    if not box_id:
        flash("A box must be selected.", "error")
        return redirect(request.url)

    try:
        box_id = int(box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)

    loc_id = None
    if location_id:
        try:
            loc_id = int(location_id)
        except ValueError:
            pass

    file = addFile(
        boxID=box_id,
        locationID=loc_id,
        fileType=file_type,
        barcode=barcode or None,
        createdByStaffUserID=_current_staff_id(),
    )

    if not file:
        flash("Failed to create the part record. Please check your inputs.", "error")
        return redirect(request.url)

    flash(f"Part #{file.fileID} created successfully.", "success")
    return redirect(url_for("file_views.file_detail_page", fileID=file.fileID))


@file_views.route("/files/create/batch-file/<file_type>", methods=["GET"])
@jwt_required()
def create_batch_file_page(file_type):
    file_type = file_type.capitalize()
    return render_template(
        "batch_file.html",
        file_type=file_type,
        boxes=getAllBoxes(),
    )


@file_views.route("/files/create/batch-file/<file_type>", methods=["POST"])
@jwt_required()
def create_batch_file_action(file_type):
    file_type = file_type.capitalize()
    form = request.form

    raw_box_id = form.get("globalBoxID", "").strip()
    global_date = form.get("globalDateCreated", "").strip() or None
    global_status = form.get("globalStatus", "").strip() or None
    global_file_type = form.get("globalFileType", "").strip().capitalize() or None

    if not raw_box_id:
        flash("A global box must be selected.", "error")
        return redirect(request.url)

    if not global_file_type or global_file_type not in ["Student", "Staff"]:
        flash("A valid file type must be selected.", "error")
        return redirect(request.url)

    try:
        global_box_id = int(raw_box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)

    file_type = global_file_type
    descriptions = form.getlist("row_description[]")
    prev_desigs = form.getlist("row_prevDesig[]")
    codes = form.getlist("row_code[]")
    cert_diplomas = form.getlist("row_certDiploma[]")
    file_numbers = form.getlist("row_fileNumber[]")
    staff_titles = form.getlist("row_staffTitle[]")
    posts = form.getlist("row_post[]")
    org_units = form.getlist("row_orgUnit[]")

    staff_id = _current_staff_id()
    created = 0
    errors = 0

    for idx, desc in enumerate(descriptions):
        desc = desc.strip()
        pd = prev_desigs[idx].strip() if idx < len(prev_desigs) else ""

        if not desc and not pd:
            student_has_data = (
                (codes[idx].strip() if idx < len(codes) else "") or
                (cert_diplomas[idx].strip() if idx < len(cert_diplomas) else "")
            )
            staff_has_data = (
                (file_numbers[idx].strip() if idx < len(file_numbers) else "") or
                (staff_titles[idx].strip() if idx < len(staff_titles) else "") or
                (posts[idx].strip() if idx < len(posts) else "") or
                (org_units[idx].strip() if idx < len(org_units) else "")
            )
            if not student_has_data and not staff_has_data:
                continue

        file = addFile(
            boxID=global_box_id,
            fileType=file_type,
            description=desc or None,
            previousDesignation=pd or None,
            dateCreated=global_date,
            createdByStaffUserID=staff_id,
            status=global_status,
        )

        if not file:
            errors += 1
            continue

        if file_type == "Student":
            create_student_record(
                fileID=file.fileID,
                code=codes[idx].strip() if idx < len(codes) else None,
                certificateDiploma=cert_diplomas[idx].strip() if idx < len(cert_diplomas) else None,
            )
        elif file_type == "Staff":
            create_staff_record(
                fileID=file.fileID,
                fileNumber=file_numbers[idx].strip() if idx < len(file_numbers) else None,
                fileTitle=staff_titles[idx].strip() if idx < len(staff_titles) else None,
                post=posts[idx].strip() if idx < len(posts) else None,
                organisationUnit=org_units[idx].strip() if idx < len(org_units) else None,
            )

        created += 1

    if created == 0 and errors == 0:
        flash("No data was entered — nothing was saved.", "warning")
    elif errors:
        flash(f"{created} record(s) saved; {errors} row(s) failed.", "warning")
    else:
        flash(f"{created} record(s) created successfully.", "success")

    return redirect(url_for("file_views.get_files_page"))


@file_views.route("/files/create/batch-part/<file_type>", methods=["GET"])
@jwt_required()
def create_batch_part_page(file_type):
    file_type = file_type.capitalize()
    return render_template(
        "batch_part.html",
        file_type=file_type,
        boxes=getAllBoxes(),
        locations=get_all_locations(),
        parent_files=searchFile(fileType=file_type) or [],
    )


@file_views.route("/files/create/batch-part/<file_type>", methods=["POST"])
@jwt_required()
def create_batch_part_action(file_type):
    file_type = file_type.capitalize()
    form = request.form

    raw_box_id = form.get("globalBoxID", "").strip()
    raw_loc_id = form.get("globalLocationID", "").strip() or None

    if not raw_box_id:
        flash("A global box must be selected.", "error")
        return redirect(request.url)

    try:
        global_box_id = int(raw_box_id)
    except ValueError:
        flash("Invalid box selection.", "error")
        return redirect(request.url)

    global_loc_id = None
    if raw_loc_id:
        try:
            global_loc_id = int(raw_loc_id)
        except ValueError:
            pass

    file_ids = form.getlist("row_fileID[]")
    barcodes = form.getlist("row_barcode[]")

    staff_id = _current_staff_id()
    created = 0
    errors = 0

    for idx, fid in enumerate(file_ids):
        fid = fid.strip()
        if not fid:
            continue

        barcode = barcodes[idx].strip() if idx < len(barcodes) else None

        file = addFile(
            boxID=global_box_id,
            locationID=global_loc_id,
            fileType=file_type,
            barcode=barcode or None,
            createdByStaffUserID=staff_id,
        )

        if not file:
            errors += 1
            continue

        created += 1

    if created == 0 and errors == 0:
        flash("No rows had a file selected — nothing was saved.", "warning")
    elif errors:
        flash(f"{created} part(s) saved; {errors} row(s) failed.", "warning")
    else:
        flash(f"{created} part(s) created successfully.", "success")

    return redirect(url_for("file_views.get_files_page"))


# ─────────────────────────────────────────────────────────────────────────────
# EXISTING ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@file_views.route("/files/create", methods=["POST"])
@jwt_required()
def add_file_page():
    box_id = request.form.get("boxID", "").strip()
    file_type = request.form.get("fileType", "").strip()
    description = request.form.get("description", "").strip() or None
    prev_desig = request.form.get("previousDesignation", "").strip() or None
    date_created = request.form.get("dateCreated", "").strip() or None
    barcode = request.form.get("barcode", "").strip() or None

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
        createdByStaffUserID=_current_staff_id(),
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
        return redirect(url_for("file_views.get_files_page"))
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
    return jsonify({
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
    }), 200


@file_views.route("/files/<int:fileID>/detail", methods=["GET"])
@jwt_required()
def file_detail_page(fileID):
    file = viewFile(fileID)
    if not file:
        flash(f"File {fileID} not found.", "error")
        return redirect(url_for("file_views.get_files_page"))
    patrons = get_all_patrons()
    return render_template("file_detail.html", file=file, patrons=patrons)


@file_views.route("/files", methods=["GET"])
@jwt_required()
def get_files_page():
    keyword = request.args.get("keyword", "").strip() or None
    fileType = request.args.get("fileType", "").strip() or None
    status = request.args.get("status", "").strip() or None
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip() or None
    page = request.args.get("page", 1, type=int)

    files = searchFile(
        keyword=keyword,
        fileType=fileType,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )

    per_page = 10
    total = len(files)
    start = (page - 1) * per_page
    paginated_files = files[start:start + per_page]
    total_pages = max(1, (total + per_page - 1) // per_page)

    return render_template(
        "files.html",
        files=paginated_files,
        boxes=getAllBoxes(),
        keyword=keyword or "",
        fileType=fileType or "",
        status=status or "",
        date_from=date_from or "",
        date_to=date_to or "",
        page=page,
        total_pages=total_pages,
        total_results=total,
    )


@file_views.route("/api/files", methods=["GET"])
@jwt_required()
def get_all_files():
    files = getAllFiles()
    if not files:
        return jsonify({"message": "No files found"}), 404
    return jsonify([
        {
            "fileID": f.fileID,
            "boxID": f.boxID,
            "fileType": f.fileType,
            "description": f.description,
            "status": f.status,
            "dateCreated": str(f.dateCreated),
        }
        for f in files
    ]), 200


@file_views.route("/api/files/search", methods=["GET"])
@jwt_required()
def search_file():
    files = searchFile(
        fileID=request.args.get("fileID"),
        fileType=request.args.get("fileType"),
        locationID=request.args.get("locationID"),
        loanID=request.args.get("loanID"),
        status=request.args.get("status"),
        keyword=request.args.get("keyword"),
    )
    if not files:
        return jsonify({"message": "No files found"}), 404
    return jsonify([
        {
            "fileID": f.fileID,
            "fileType": f.fileType,
            "status": f.status,
            "description": f.description,
            "locationID": f.locationID,
            "boxID": f.boxID,
        }
        for f in files
    ]), 200


@file_views.route("/files/<int:fileID>/status", methods=["PUT"])
@jwt_required()
def change_file_status(fileID):
    data = request.json
    if not data or "status" not in data:
        return jsonify({"error": "Status is required"}), 400

    file = changeFileStatus(fileID, data["status"])
    if not file:
        return jsonify({"error": "File not found or invalid status"}), 404
    return jsonify({
        "message": f"File {fileID} status updated successfully",
        "status": file.status,
    }), 200