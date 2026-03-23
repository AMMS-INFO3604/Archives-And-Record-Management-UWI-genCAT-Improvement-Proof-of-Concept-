from flask import Blueprint, request, jsonify, render_template, send_file
from datetime import datetime, timezone
from typing import Optional

import barcode
from barcode.writer import ImageWriter
import io
import base64

 
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
 
def generate_barcode_b64(value: str) -> str:
    """
    Generate a Code128 barcode for *value* and return it as a
    base64-encoded PNG string (used by the /api/barcode/generate route).
    """
    code = barcode.get('code128', value, writer=ImageWriter())
    buf  = io.BytesIO()
    code.write(buf, options={
        'write_text':    True,
        'module_height': 12.0,
        'font_size':     8,
        'text_distance': 3,
        'quiet_zone':    4,
    })
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')
 
 
def generate_barcode_png_bytes(value: str) -> bytes:
    """
    Return raw PNG bytes for a Code128 barcode
    (used by the /api/barcode/download route).
    """
    code = barcode.get('code128', value, writer=ImageWriter())
    buf  = io.BytesIO()
    code.write(buf, options={
        'write_text':    True,
        'module_height': 12.0,
        'font_size':     8,
        'text_distance': 3,
        'quiet_zone':    6,
    })
    buf.seek(0)
    return buf.read()
 
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
    
@barcode_views.route('/api/barcode/generate', methods=['POST'])
def api_generate_barcode():
    """
    POST /api/barcode/generate
    Body: { "value": "BOX-A-001" }
    Returns: { "barcode_b64": "<base64 PNG string>" }
 
    Called by the Generate button in the Add Box / Add File modals.
    The modal displays the returned image as:
        <img src="data:image/png;base64,<barcode_b64>" />
    """
    data  = request.get_json(silent=True) or {}
    value = (data.get('value') or '').strip()
 
    if not value:
        return jsonify({"error": "value is required"}), 400
 
    try:
        b64 = generate_barcode_b64(value)
        return jsonify({"barcode_b64": b64, "value": value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
@barcode_views.route('/api/barcode/download/<path:value>', methods=['GET'])
def api_download_barcode(value: str):
    """
    GET /api/barcode/download/BOX-A-001
    Returns the barcode as a downloadable PNG file.
 
    Called by the "Download PNG" button in the modal barcode preview.
    """
    try:
        png  = generate_barcode_png_bytes(value)
        buf  = io.BytesIO(png)
        buf.seek(0)
        safe = value.replace('/', '-').replace('\\', '-')
        return send_file(
            buf,
            mimetype='image/png',
            as_attachment=True,
            download_name=f"barcode-{safe}.png",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500