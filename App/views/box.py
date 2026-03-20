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
# HTML – Detail page
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes/<int:box_id>/detail", methods=["GET"])
@jwt_required()
def get_box_details_page(box_id):
    box = getBoxByID(box_id)
    if not box:
        flash("Box not found.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
    all_locations = get_all_locations()
    # Need locations for the 'Add File' modal in detail page
    return render_template("box_detail.html", box=box, locations=all_locations)
 
 
# ---------------------------------------------------------------------------
# HTML – List page
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes", methods=["GET"])
@jwt_required()
def get_boxes_page():
    """Render the box list page with an optional location filter."""
    selected_location = request.args.get("location", "").strip()
 
    all_locations = get_all_locations()
    # Format as "GeoLocation, Campus" for consistent display
    loc_names = [f"{loc.geoLocation}, {loc.campus}" for loc in all_locations]
 
    if selected_location and selected_location != "all":
        # Handle "GeoLocation, Campus" string
        parts = selected_location.split(', ')
        geo = parts[0]
        camp = parts[1] if len(parts) > 1 else None
        
        target_loc = next((loc for loc in all_locations if loc.geoLocation == geo and (not camp or loc.campus == camp)), None)
        if target_loc:
            boxes = searchBoxesByLocation(target_loc.locationID)
        else:
            boxes = getAllBoxes()
            selected_location = ""
    else:
        boxes = getAllBoxes()
 
    return render_template(
        "boxes.html",
        boxes=boxes,
        locations=loc_names,
        selected_location=selected_location,
    )
 
 
# ---------------------------------------------------------------------------
# HTML – Create (form POST)
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes", methods=["POST"])
@jwt_required()
def create_box_action():
    """Handle the add-box form submitted from the boxes page."""
    boxID = request.form.get("boxID", "").strip()
    location_name = request.form.get("location", "").strip()
    aisle = request.form.get("aisle", "").strip()
    rack = request.form.get("rack", "").strip()
    shelf = request.form.get("shelf", "").strip()
 
    if not boxID or not location_name:
        flash("Box ID and location are required.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    all_locations = get_all_locations()
    target_loc = next((loc for loc in all_locations if loc.geoLocation == location_name), None)
    
    if not target_loc:
        flash(f"Location '{location_name}' not found.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    # The addBox controller expects bayNo, rowNo, columnNo
    # We'll map aisle/rack/shelf to these or update the model if possible.
    # For now, let's try to pass them as strings if model allows, or convert to int if needed.
    # Looking at initialize.py, it uses ints for bayNo, rowNo, columnNo.
    try:
        bay = int(aisle) if aisle.isdigit() else 0
        row = int(rack) if rack.isdigit() else 0
        col = int(shelf) if shelf.isdigit() else 0
    except ValueError:
        bay, row, col = 0, 0, 0

    box = addBox(
        bayNo=bay,
        rowNo=row,
        columnNo=col,
        barcode=boxID,
        locationID=target_loc.locationID,
    )
 
    if box:
        flash(f"Box {box.boxID} created successfully.", "success")
    else:
        flash("Failed to create box. ID might already exist.", "error")
 
    return redirect(url_for("box_views.get_boxes_page"))
 
 
# ---------------------------------------------------------------------------
# HTML – Move location (form POST)
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes/<int:box_id>/move", methods=["POST"])
@jwt_required()
def move_box_action(box_id):
    """Move a box to a new location via an HTML form."""
    location_name = request.form.get("location", "").strip()
    aisle = request.form.get("aisle", "").strip()
    rack = request.form.get("rack", "").strip()
    shelf = request.form.get("shelf", "").strip()
 
    if not location_name:
        flash("Location is required.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    all_locations = get_all_locations()
    target_loc = next((loc for loc in all_locations if loc.geoLocation == location_name), None)
    
    if not target_loc:
        flash(f"Location '{location_name}' not found.", "error")
        return redirect(url_for("box_views.get_boxes_page"))
 
    # Using existing controller which might only update locationID
    box = moveBoxLocation(box_id, target_loc.locationID)
    if box:
        # Also update the coordinates if they were provided
        if aisle or rack or shelf:
            updateBox(
                boxID=box_id,
                bayNo=int(aisle) if aisle.isdigit() else box.bayNo,
                rowNo=int(rack) if rack.isdigit() else box.rowNo,
                columnNo=int(shelf) if shelf.isdigit() else box.columnNo,
                locationID=target_loc.locationID
            )
        flash(f"Box {box_id} moved successfully.", "success")
    else:
        flash(f"Failed to move box {box_id}.", "error")
 
    return redirect(url_for("box_views.get_boxes_page"))
 
 
# ---------------------------------------------------------------------------
# HTML – Delete (form POST)
# ---------------------------------------------------------------------------
 
@box_views.route("/boxes/<int:box_id>/delete", methods=["POST"])
@jwt_required()
def delete_box_action(box_id):
    """Delete a box via an HTML form."""
    success = deleteBox(box_id)
    if success:
        flash(f"Box {box_id} deleted successfully.", "success")
    else:
        flash(f"Box {box_id} not found or could not be deleted.", "error")
    return redirect(url_for("box_views.get_boxes_page"))
 
 
# ---------------------------------------------------------------------------
# API routes (rest unchanged)
# ---------------------------------------------------------------------------
# ... rest of the file ...
