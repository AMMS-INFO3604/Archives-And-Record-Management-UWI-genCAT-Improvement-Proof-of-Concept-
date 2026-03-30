from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_jwt_extended import current_user, jwt_required

from App.controllers.location import (
    create_location,
    delete_location,
    get_all_locations,
    get_all_locations_json,
    get_boxes_at_location_json,
    get_files_at_location_json,
    get_location,
    get_location_json,
    search_locations,
    update_location,
)

location_views = Blueprint("location_views", __name__, template_folder="../templates")


# ---------------------------------------------------------------------------
# Page / Action Routes
# ---------------------------------------------------------------------------


@location_views.route("/location", methods=["GET"])
@jwt_required()
def get_locations_page():
    from flask import session
    loc = request.args.get("loc")
    if loc:
        session["selected_location"] = loc
        return redirect(url_for("box_views.get_boxes_page"))
    
    locations = get_all_locations()
    return render_template("location.html", locations=locations)


@location_views.route("/location/<int:locationID>", methods=["GET"])
@jwt_required()
def get_location_page(locationID):
    location = get_location(locationID)
    if not location:
        flash(f"Location {locationID} not found.", "error")
        return redirect(url_for("location_views.get_locations_page"))
    return render_template("location.html", locations=[location])


@location_views.route("/location", methods=["POST"])
@jwt_required()
def create_location_action():
    data = request.form
    geoLocation = data.get("geoLocation", "").strip()
    if not geoLocation:
        flash("Location name is required.", "error")
        return redirect(url_for("location_views.get_locations_page"))
    location = create_location(geoLocation)
    if location:
        flash(f'Location "{geoLocation}" created successfully.', "success")
    else:
        flash("Failed to create location.", "error")
    return redirect(url_for("location_views.get_locations_page"))


@location_views.route("/location/<int:locationID>", methods=["POST"])
@jwt_required()
def update_location_action(locationID):
    data = request.form
    geoLocation = data.get("geoLocation", "").strip()
    if not geoLocation:
        flash("Location name is required.", "error")
        return redirect(url_for("location_views.get_locations_page"))
    location = update_location(locationID, geoLocation)
    if location:
        flash(f"Location {locationID} updated successfully.", "success")
    else:
        flash(f"Location {locationID} not found.", "error")
    return redirect(url_for("location_views.get_locations_page"))


@location_views.route("/location/<int:locationID>/delete", methods=["POST"])
@jwt_required()
def delete_location_action(locationID):
    success = delete_location(locationID)
    if success:
        flash(f"Location {locationID} deleted successfully.", "success")
    else:
        flash(f"Location {locationID} not found.", "error")
    return redirect(url_for("location_views.get_locations_page"))


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------


@location_views.route("/api/locations", methods=["GET"])
@jwt_required()
def get_locations_api():
    return jsonify(get_all_locations_json()), 200


@location_views.route("/api/locations/search", methods=["GET"])
@jwt_required()
def search_locations_api():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400
    results = search_locations(query)
    return jsonify([loc.get_json() for loc in results]), 200


@location_views.route("/api/locations/<int:locationID>", methods=["GET"])
@jwt_required()
def get_location_api(locationID):
    location = get_location_json(locationID)
    if not location:
        return jsonify({"error": f"Location {locationID} not found"}), 404
    return jsonify(location), 200


@location_views.route("/api/locations", methods=["POST"])
@jwt_required()
def create_location_api():
    data = request.json
    if not data or not data.get("geoLocation"):
        return jsonify({"error": "geoLocation is required"}), 400
    location = create_location(data["geoLocation"].strip())
    if not location:
        return jsonify({"error": "Failed to create location"}), 500
    return jsonify(
        {
            "message": "Location created successfully",
            **location.get_json(),
        }
    ), 201


@location_views.route("/api/locations/<int:locationID>", methods=["PUT"])
@jwt_required()
def update_location_api(locationID):
    data = request.json
    if not data or not data.get("geoLocation"):
        return jsonify({"error": "geoLocation is required"}), 400
    location = update_location(locationID, data["geoLocation"].strip())
    if not location:
        return jsonify({"error": f"Location {locationID} not found"}), 404
    return jsonify(
        {
            "message": "Location updated successfully",
            **location.get_json(),
        }
    ), 200


@location_views.route("/api/locations/<int:locationID>", methods=["DELETE"])
@jwt_required()
def delete_location_api(locationID):
    success = delete_location(locationID)
    if not success:
        return jsonify({"error": f"Location {locationID} not found"}), 404
    return jsonify({"message": f"Location {locationID} deleted successfully"}), 200


@location_views.route("/api/locations/<int:locationID>/boxes", methods=["GET"])
@jwt_required()
def get_location_boxes_api(locationID):
    boxes = get_boxes_at_location_json(locationID)
    if boxes is None:
        return jsonify({"error": f"Location {locationID} not found"}), 404
    return jsonify(boxes), 200


@location_views.route("/api/locations/<int:locationID>/files", methods=["GET"])
@jwt_required()
def get_location_files_api(locationID):
    if not get_location(locationID):
        return jsonify({"error": f"Location {locationID} not found"}), 404
    files = get_files_at_location_json(locationID)
    return jsonify(files), 200
