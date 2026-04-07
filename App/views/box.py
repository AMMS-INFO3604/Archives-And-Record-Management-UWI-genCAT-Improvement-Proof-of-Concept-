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
 
from App.controllers.box import (
    addBox,
    changeBoxStatus,
    deleteBox,
    getAllBoxes,
    getAllBoxesJSON,
    getBoxByID,
    getBoxJSON,
    moveBoxLocation,
    searchBoxesByLocation,
    searchBoxesByLocationJSON,
    updateBox,
)
from App.controllers.file import (
    deleteFile,
    updateFile,
    viewFile,
)
from App.controllers.location import get_all_locations
 
box_views = Blueprint("box_views", __name__, template_folder="templates")
 
 
# ---------------------------------------------------------------------------
# HTML – Detail page
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes/<int:boxID>/detail", methods=["GET"])
@jwt_required()
def get_box_detail_page(boxID):
    box = getBoxByID(boxID)
    if not box:
        flash("Box not found.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
    all_boxes = getAllBoxes()
    return render_template("box_detail.html", box=box, all_boxes=all_boxes)
 
 
# ---------------------------------------------------------------------------
# HTML – List page
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes", methods=["GET"])
@jwt_required()
def get_boxes_page():
    """Render the box list page with an optional location filter."""
    location_id_raw = request.args.get("locationID", "").strip()
 
    all_locations = get_all_locations()
 
    if location_id_raw:
        try:
            location_id = int(location_id_raw)
            boxes = searchBoxesByLocation(location_id)
        except (ValueError, TypeError):
            boxes = getAllBoxes()
            location_id_raw = ""
    else:
        boxes = getAllBoxes()
 
    return render_template(
        "boxes.html",
        boxes=boxes,
        locations=all_locations,
        location_filter=location_id_raw,
    )
 
 
# ---------------------------------------------------------------------------
# HTML – Create (form POST)
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes", methods=["POST"])
@jwt_required()
def add_box_page():
    """Handle the add-box form submitted from the boxes page."""
    bay_no = request.form.get("bayNo", "").strip()
    row_no = request.form.get("rowNo", "").strip()
    col_no = request.form.get("columnNo", "").strip()
    barcode = request.form.get("barcode", "").strip() or None
    location_id = request.form.get("locationID", "").strip()
 
    if not bay_no or not row_no or not col_no or not location_id:
        flash("Bay, row, column and location are all required.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    try:
        bay_no = int(bay_no)
        row_no = int(row_no)
        col_no = int(col_no)
        location_id = int(location_id)
    except ValueError:
        flash("Bay, row, column and location must be whole numbers.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    box = addBox(
        bayNo=bay_no,
        rowNo=row_no,
        columnNo=col_no,
        barcode=barcode,
        locationID=location_id,
    )
 
    if box:
        flash(f"Box #{box.boxID} created successfully.", "success")
    else:
        flash(
            "Failed to create box. Check that the location exists and the barcode is unique.",
            "error",
        )
 
    return redirect(url_for("box_views.get_boxes_page"))
 
 
# ---------------------------------------------------------------------------
# HTML – Move location (form POST)
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes/<int:boxID>/move", methods=["POST"])
@jwt_required()
def move_box_page(boxID):
    """Move a box to a new location via an HTML form."""
    new_location_raw = request.form.get("newLocationID", "").strip()
 
    if not new_location_raw:
        flash("A new location is required.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    try:
        new_location_id = int(new_location_raw)
    except ValueError:
        flash("Location ID must be a whole number.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    box = moveBoxLocation(boxID, new_location_id)
    if box:
        flash(f"Box #{boxID} moved to location #{new_location_id}.", "success")
    else:
        flash(f"Failed to move box #{boxID}. Check that both IDs are valid.", "error")
 
    return redirect(url_for("box_views.get_boxes_page"))
 
 
# ---------------------------------------------------------------------------
# HTML – Delete (form POST)
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes/<int:boxID>/delete", methods=["POST"])
@jwt_required()
def delete_box_page(boxID):
    """Delete a box via an HTML form."""
    success = deleteBox(boxID)
    if success:
        flash(f"Box #{boxID} deleted successfully.", "success")
    else:
        flash(f"Box #{boxID} not found or could not be deleted.", "error")
    return redirect(url_for("box_views.get_boxes_page"))
 
 
# ---------------------------------------------------------------------------
# HTML – Change Status (form POST from detail page)
# ---------------------------------------------------------------------------

@box_views.route("/boxes/<int:boxID>/status", methods=["POST"])
@jwt_required()
def change_box_status_page(boxID):
    """Change a box's colour/status label via an HTML form on the detail page."""
    color_status = request.form.get("colorStatus", "").strip()

    if not color_status:
        flash("A status value is required.", "error")
        return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))

    box = changeBoxStatus(boxID, color_status)
    if box:
        flash(f"Box #{boxID} status updated to '{color_status}'.", "success")
    else:
        flash(f"Failed to update status for Box #{boxID}.", "error")

    return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))


# ---------------------------------------------------------------------------
# HTML – Assign existing file to box (form POST from detail page)
# ---------------------------------------------------------------------------

@box_views.route("/boxes/<int:boxID>/files/add", methods=["POST"])
@jwt_required()
def add_file_to_box_page(boxID):
    """Reassign an existing file into this box from the detail page."""
    file_id_raw = request.form.get("fileID", "").strip()

    if not file_id_raw:
        flash("A file must be selected.", "error")
        return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))

    try:
        file_id = int(file_id_raw)
    except ValueError:
        flash("Invalid file ID.", "error")
        return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))

    file = updateFile(fileID=file_id, boxID=boxID)
    if file:
        flash(f"File #{file_id} assigned to Box #{boxID}.", "success")
    else:
        flash(f"Failed to assign File #{file_id} to this box.", "error")

    return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))


# ---------------------------------------------------------------------------
# HTML – Move file to another box (form POST from detail page)
# ---------------------------------------------------------------------------

@box_views.route("/boxes/<int:boxID>/files/<int:fileID>/move", methods=["POST"])
@jwt_required()
def move_file_to_box_page(boxID, fileID):
    """Move a file to a different box from the detail page."""
    new_box_raw = request.form.get("newBoxID", "").strip()

    if not new_box_raw:
        flash("A destination box is required.", "error")
        return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))

    try:
        new_box_id = int(new_box_raw)
    except ValueError:
        flash("Invalid box ID.", "error")
        return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))

    file = updateFile(fileID=fileID, boxID=new_box_id)
    if file:
        flash(f"File #{fileID} moved to Box #{new_box_id}.", "success")
    else:
        flash(f"Failed to move File #{fileID}.", "error")

    return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))


# ---------------------------------------------------------------------------
# HTML – Delete file from box (form POST from detail page)
# ---------------------------------------------------------------------------

@box_views.route("/boxes/<int:boxID>/files/<int:fileID>/delete", methods=["POST"])
@jwt_required()
def delete_file_from_box_page(boxID, fileID):
    """Delete a file from the box detail page."""
    success = deleteFile(fileID)
    if success:
        flash(f"File #{fileID} deleted successfully.", "success")
    else:
        flash(f"File #{fileID} could not be deleted.", "error")

    return redirect(url_for("box_views.get_box_detail_page", boxID=boxID))


# ---------------------------------------------------------------------------
# API – Create
# ---------------------------------------------------------------------------
 
@box_views.route("/api/boxes", methods=["POST"])
@jwt_required()
def api_add_box():
    data = request.json
    if not data:
        return jsonify({"message": "No input data provided"}), 400
 
    box = addBox(
        bayNo=data.get("bayNo"),
        rowNo=data.get("rowNo"),
        columnNo=data.get("columnNo"),
        barcode=data.get("barcode"),
        locationID=data.get("locationID"),
    )
 
    if not box:
        return jsonify({"message": "Failed to add box"}), 400
    return jsonify({"message": "Box added successfully", "box": getBoxJSON(box)}), 201
 
 
# ---------------------------------------------------------------------------
# API – Read (all)
# ---------------------------------------------------------------------------
 
@box_views.route("/api/boxes", methods=["GET"])
@jwt_required()
def api_get_all_boxes():
    boxes = getAllBoxesJSON()
    if not boxes:
        return jsonify({"message": "No boxes found"}), 404
    return jsonify(boxes), 200
 
 
# ---------------------------------------------------------------------------
# API – Read (single)
# ---------------------------------------------------------------------------
 
@box_views.route("/api/boxes/<int:boxID>", methods=["GET"])
@jwt_required()
def api_get_box_by_id(boxID):
    box = getBoxByID(boxID)
    if not box:
        return jsonify({"message": f"Box {boxID} not found"}), 404
    return jsonify(getBoxJSON(box)), 200
 
 
# ---------------------------------------------------------------------------
# API – Search by location
# ---------------------------------------------------------------------------
 
@box_views.route("/api/boxes/search", methods=["GET"])
@jwt_required()
def api_search_boxes_by_location():
    location_id = request.args.get("locationID")
    if not location_id:
        return jsonify({"message": "locationID query parameter is required"}), 400
 
    try:
        location_id = int(location_id)
    except (ValueError, TypeError):
        return jsonify({"message": "locationID must be a whole number"}), 400
 
    boxes = searchBoxesByLocationJSON(location_id)
    if not boxes:
        return jsonify({"message": f"No boxes found for location {location_id}"}), 404
    return jsonify(boxes), 200
 
 
# ---------------------------------------------------------------------------
# API – Update
# ---------------------------------------------------------------------------
 
@box_views.route("/api/boxes/<int:boxID>", methods=["PUT"])
@jwt_required()
def api_update_box(boxID):
    data = request.json
    if not data:
        return jsonify({"message": "No input data was provided"}), 400
 
    box = updateBox(
        boxID=boxID,
        bayNo=data.get("bayNo"),
        rowNo=data.get("rowNo"),
        columnNo=data.get("columnNo"),
        barcode=data.get("barcode"),
        locationID=data.get("locationID"),
    )
 
    if not box:
        return jsonify({"message": f"Box {boxID} not found or update failed"}), 404
    return jsonify({"message": "Box updated successfully", "box": getBoxJSON(box)}), 200
 
 
# ---------------------------------------------------------------------------
# API – Move location
# ---------------------------------------------------------------------------
 
@box_views.route("/api/boxes/<int:boxID>/move", methods=["PUT"])
@jwt_required()
def api_move_box_location(boxID):
    data = request.json
    if not data or "newLocationID" not in data:
        return jsonify({"message": "newLocationID is required"}), 400
 
    box = moveBoxLocation(boxID, data["newLocationID"])
    if not box:
        return jsonify({"message": f"Failed to move box {boxID}"}), 400
 
    return jsonify(
        {
            "message": f"Box {boxID} moved successfully",
            "boxID": box.boxID,
            "newLocationID": box.locationID,
        }
    ), 200
 
 
# ---------------------------------------------------------------------------
# API – Delete
# ---------------------------------------------------------------------------
 
@box_views.route("/api/boxes/<int:boxID>", methods=["DELETE"])
@jwt_required()
def api_delete_box(boxID):
    success = deleteBox(boxID)
    if not success:
        return jsonify(
            {"message": f"Box {boxID} not found or could not be deleted"}
        ), 404
    return jsonify({"message": f"Box {boxID} deleted successfully"}), 200