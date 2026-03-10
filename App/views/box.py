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
from App.controllers.location import get_all_locations

box_views = Blueprint("box_views", __name__, template_folder="templates")


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
