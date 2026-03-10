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

from App.controllers.box import (
    addBox,
    deleteBox,
    getAllBoxes,
    getBoxByID,
    moveBoxLocation,
    searchBoxesByLocation,
    updateBox,
)
from App.database import db
from App.models import Box

from .index import index_views

box_views = Blueprint("box_views", __name__, template_folder="templates")

@box_views.route("/boxes", methods=["GET"])
@jwt_required()
def get_boxes_page():
    keyword = request.args.get("keyword", "").strip()
    boxes = searchBoxesByBarcode(keyword) if keyword else getAllBoxes()
    return render_template("boxes.html", boxes=boxes, keyword=keyword)


@box_views.route("/boxes/<int:boxID>/detail", methods=["GET"])
@jwt_required()
def get_box_detail_page(boxID):
    box = getBoxByID(boxID)
    if not box:
        flash("Box not found.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
    return render_template("box_detail.html", box=box)

@box_views.route("/api/boxes", methods=["POST"])
@jwt_required()
def add_box():
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
    return jsonify({"message": "Box added successfully", "box": box}), 201


@box_views.route("/api/boxes/<int:boxID>", methods=["PUT"])
@jwt_required()
def update_box(boxID):
    data = request.json

    if not data:
        return jsonify({"message": "No input data was provided"}), 400

    box = updateBox(
        boxID=data.get("boxID"),
        bayNo=data.get("bayNo"),
        rowNo=data.get("rowNo"),
        columnNo=data.get("columnNo"),
        barcode=data.get("barcode"),
        locationID=data.get("locationID"),
    )

    if not box:
        return jsonify({"message": "Failed to update box"}), 400
    return jsonify({"message": "Box updated successfully", "box": box}), 200


@box_views.route("/api/boxes/<int:boxID>/move", methods=["PUT"])
@jwt_required()
def move_box_location(boxID):
    data = request.json

    if not data or "newLocationID" not in data:
        return jsonify({"message": "newLocationID is required"}), 400

    box = moveBoxLocation(boxID, data["newLocationID"])

    if not box:
        return jsonify({"message": "Failed to move box"}), 400
    return jsonify(
        {
            "message": f"Box {boxID} moved successfully",
            "boxID": box.boxID,
            "newLocationID": box.locationID,
        }
    ), 200


@box_views.route("/api/boxes/<int:boxID>", methods=["DELETE"])
@jwt_required()
def delete_box(boxID):
    box = deleteBox(boxID)

    if not box:
        return jsonify({"message": "Failed to delete box"}), 400
    return jsonify({"message": f"Box {boxID} deleted successfully"}), 200


@box_views.route("/api/boxes/<int:boxID>", methods=["GET"])
@jwt_required()
def get_box_by_id(boxID):
    box = getBoxByID(boxID)

    if not box:
        return jsonify({"message": f"Box {boxID} not found"}), 404
    return jsonify({"box": box}), 200


@box_views.route("/boxes", methods=["GET"])
@jwt_required()
def get_all_boxes():
    boxes = getAllBoxes()

    if not boxes:
        return jsonify({"message": "No boxes found"}), 404
    return jsonify({"boxes": boxes}), 200


@box_views.route("/api/boxes/search/<int:locationID>", methods=["GET"])
@jwt_required()
def search_boxes_by_location(locationID):
    locationID = request.args.get("locationID")

    if not locationID:
        return jsonify({"message": "Location ID is required"}), 400

    boxes = searchBoxesByLocation(locationID)

    if not boxes:
        return jsonify(
            {"message": f"No boxes found for location with ID {locationID}"}
        ), 404
    return jsonify({"boxes": boxes}), 200
