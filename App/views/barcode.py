from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timezone
from typing import Optional
 
barcode_views = Blueprint('barcode', __name__, template_folder='../templates')
 
# ── Demo DB stand-in ──────────────────────────────────────────────────────────
# Replace get_record_by_id() below with a real DB query using your models.
# Example using your existing models:
#   from App.models.file_record import FileRecord
#   record = FileRecord.query.filter_by(id=record_id).first()
_DEMO_DB = {
    "FILE-0001": {"id": "FILE-0001", "name": "Contract A",   "location": "Cabinet 1 / Shelf 2", "category": "Legal",   "created_at": "2024-01-10"},
    "FILE-0002": {"id": "FILE-0002", "name": "Invoice Pack", "location": "Cabinet 3 / Shelf 1", "category": "Finance", "created_at": "2024-02-05"},
    "FILE-0003": {"id": "FILE-0003", "name": "HR Folder",    "location": "Cabinet 2 / Shelf 4", "category": "HR",      "created_at": "2024-03-01"},
}
# ─────────────────────────────────────────────────────────────────────────────
 
 
def get_record_by_id(record_id: str) -> Optional[dict]:
    """
    Look up a physical file by its barcode ID.
    Replace this with a real DB query, e.g.:
        from App.models.file_record import FileRecord
        row = FileRecord.query.filter_by(id=record_id).first()
        return {"id": row.id, "name": row.name, ...} if row else None
    """
    return _DEMO_DB.get(record_id)
 
 
def log_scan_event(record_id: str, found: bool) -> None:
    """
    Optionally persist a scan event for audit purposes.
    Replace with a real DB insert using your ScanEvent model if you have one.
    """
    status = "FOUND" if found else "NOT FOUND"
    print(f"[SCAN] {datetime.now(timezone.utc).isoformat()}  {status}  {record_id}")
 
 
# ── Scanner page ──────────────────────────────────────────────────────────────
@barcode_views.route('/scanner', methods=['GET'])
def scanner_page():
    return render_template('scanner.html')
 
 
# ── Lookup API ────────────────────────────────────────────────────────────────
@barcode_views.route('/api/barcode/lookup/<record_id>', methods=['GET'])
def lookup_barcode(record_id: str):
    """
    GET /api/barcode/lookup/<record_id>
    Called by the scanner page after a barcode is decoded.
    Returns JSON with the matching file record or a not-found response.
    """
    record     = get_record_by_id(record_id.strip())
    found      = record is not None
    scanned_at = datetime.now(timezone.utc).isoformat()
 
    log_scan_event(record_id, found)
 
    if found:
        return jsonify({
            "found":      True,
            "record":     record,
            "scanned_at": scanned_at,
            "message":    "Record found.",
        })
 
    return jsonify({
        "found":      False,
        "record":     None,
        "scanned_at": scanned_at,
        "message":    f"No record found for ID '{record_id}'.",
    }), 404