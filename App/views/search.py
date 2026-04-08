from flask import Blueprint, jsonify, request
from App.models import File, Box, Location
from App.database import db

search_views = Blueprint("search_views", __name__, template_folder="../templates")

@search_views.route("/api/search", methods=["GET"])
def global_search():
    query = request.args.get("q", "").lower().strip()
    if not query:
        return jsonify([])
        
    results = []

    # Search Files
    files = File.query.all()
    for f in files:
        if query in (f.description or "").lower() or query in (f.previousDesignation or "").lower() or query in str(f.fileID) or query in (f.barcode or "").lower():
            results.append({
                "id": f.fileID,
                "type": "File",
                "label": f.description or f"File {f.fileID}",
                "sublabel": f"ID: {f.fileID} | {f.fileType}",
                "url": f"/files/{f.fileID}/detail"
            })

    # Search Boxes
    boxes = Box.query.all()
    for b in boxes:
        if query in (b.barcode or "").lower() or query in str(b.boxID):
            results.append({
                "id": b.boxID,
                "type": "Box",
                "label": b.barcode or f"Box {b.boxID}",
                "sublabel": f"ID: {b.boxID} | Bay: {b.bayNo}, Row: {b.rowNo}, Col: {b.columnNo}",
                "url": f"/boxes/{b.boxID}/detail"
            })

    # Search Locations
    locations = Location.query.all()
    for l in locations:
        if query in (l.geoLocation or "").lower():
            results.append({
                "id": l.locationID,
                "type": "Location",
                "label": l.geoLocation,
                "sublabel": "Location",
                "url": f"/location"
            })

    # Basic ranking (exact matches or starts-with matches first)
    def rank_result(res):
        label = res["label"].lower()
        if query == label: return 0
        if label.startswith(query): return 1
        return 2

    results.sort(key=rank_result)
    
    return jsonify(results[:20])
