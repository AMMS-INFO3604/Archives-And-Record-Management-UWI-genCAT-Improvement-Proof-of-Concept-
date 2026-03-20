from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_jwt_extended import current_user, jwt_required

from App.controllers import create_user, initialize
from App.models import File, Box, Location
from App.database import db

index_views = Blueprint("index_views", __name__, template_folder="../templates")


@index_views.route("/", methods=["GET"])
@jwt_required(optional=True)
def index_page():
    if current_user:
        return render_template("index.html")
    return redirect(url_for("auth_views.staff_login_page"))

@index_views.route("/api/search/suggestions", methods=["GET"])
@jwt_required()
def search_suggestions():
    try:
        # Return all searchable items for client-side fuzzy search
        files = db.session.scalars(db.select(File)).all()
        boxes = db.session.scalars(db.select(Box)).all()
        locations = db.session.scalars(db.select(Location)).all()
        
        suggestions = []
        for f in files:
            suggestions.append({
                "id": f.fileID,
                "text": f.description or str(f.fileID),
                "sub": f.fileType,
                "status": f.status,
                "type": "File",
                "url": url_for('file_views.get_file_details_page', file_id=f.fileID)
            })
        for b in boxes:
            suggestions.append({
                "id": b.boxID,
                "text": str(b.boxID),
                "sub": f"Box in {b.location.geoLocation if b.location else 'Unknown'}",
                "type": "Box",
                "url": url_for('box_views.get_box_details_page', box_id=b.boxID)
            })
        for l in locations:
            suggestions.append({
                "id": l.locationID,
                "text": l.geoLocation,
                "sub": "Location",
                "type": "Location",
                "url": url_for('location_views.get_locations_page', loc=l.geoLocation)
            })
            
        return jsonify(suggestions)
    except Exception as e:
        print(f"Error in search_suggestions: {e}")
        return jsonify([])


@index_views.route("/init", methods=["GET"])
def init():
    initialize()
    return jsonify(message="db initialized!")


@index_views.route("/health", methods=["GET"])
@index_views.route("/healthcheck", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})
    