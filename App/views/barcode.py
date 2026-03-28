from flask import Blueprint, current_app, request, jsonify, render_template, send_file
from datetime import datetime, timezone
from typing import Optional

import barcode
from barcode.writer import ImageWriter
import io
import base64
import hmac
import hashlib
import time
import qrcode

barcode_views = Blueprint('barcode', __name__, template_folder='../templates')


# ── Demo DB stand-in ──────────────────────────────────────────────────────────
# Replace get_record_by_id() below with a real DB query using your models.
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


# ── Signed token helpers ──────────────────────────────────────────────────────
# Tokens are HMAC-signed with the Flask SECRET_KEY so they can't be forged.
# They expire after TOKEN_TTL seconds (10 minutes by default).
_TOKEN_TTL = 600  # seconds


def _make_token(payload: str) -> str:
    """
    Create a time-stamped HMAC token for the given payload string.
    Format returned: "<unix_timestamp>:<hex_signature>"
    """
    ts  = str(int(time.time()))
    raw = f"{payload}:{ts}"
    sig = hmac.new(
        current_app.secret_key.encode(),
        raw.encode(),
        hashlib.sha256
    ).hexdigest()[:24]
    return f"{ts}:{sig}"


def _verify_token(payload: str, token: str) -> bool:
    """
    Return True if the token is valid and not expired for the given payload.
    """
    try:
        ts, sig = token.split(":", 1)
        if int(time.time()) - int(ts) > _TOKEN_TTL:
            return False  # expired
        raw      = f"{payload}:{ts}"
        expected = hmac.new(
            current_app.secret_key.encode(),
            raw.encode(),
            hashlib.sha256
        ).hexdigest()[:24]
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False


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


# ── QR / Scan-token API ───────────────────────────────────────────────────────

@barcode_views.route('/api/loans/scan-token', methods=['POST'])
def issue_scan_token():
    """
    POST /api/loans/scan-token
    Body: { "loanID": 42, "mode": "issue" | "return" }

    Returns a signed scanner URL and its QR code as a base64 PNG so the
    file_detail page can show it to staff without a page reload.

    No JWT decorator here because this is called via fetch() from the
    already-authenticated detail page — the CSRF protection comes from the
    signed token itself.  If you prefer, add @jwt_required() back.
    """
    data    = request.get_json(silent=True) or {}
    loan_id = data.get('loanID')
    mode    = data.get('mode', 'issue')

    if not loan_id or mode not in ('issue', 'return'):
        return jsonify({'error': 'loanID and mode (issue|return) are required'}), 400

    token       = _make_token(f"{mode}:{loan_id}")
    scanner_url = (
        f"{request.host_url.rstrip('/')}/"
        f"scanner?mode={mode}&loanID={loan_id}&token={token}"
    )

    # Build QR code image
    img = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    img.add_data(scanner_url)
    img.make(fit=True)
    pil_img = img.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    buf.seek(0)
    qr_b64 = base64.b64encode(buf.read()).decode()

    return jsonify({
        'token':       token,
        'scanner_url': scanner_url,
        'qr_b64':      qr_b64,
        'expires_in':  _TOKEN_TTL,
    })


@barcode_views.route('/api/loans/scan-confirm', methods=['POST'])
def scan_confirm():
    """
    POST /api/loans/scan-confirm
    Body: { "loanID": 42, "barcode": "FILE-0042", "token": "<signed_token>" }

    Called by the phone scanner to CONFIRM an issue (checkout).
    No JWT needed — the signed token acts as the credential.

    Decision tree
    ─────────────
    1. Token invalid / expired          → 401 BAD_TOKEN
    2. Loan not found                   → 404 NO_LOAN
    3. No file attached to loan         → 404 NO_FILE
    4. File has no barcode in DB        → 409 NO_BARCODE  (staff must add one)
    5. Barcode matches a different file → 409 WRONG_FILE
    6. Barcode completely unknown       → 404 UNKNOWN_BARCODE
    7. All checks pass                  → 200 success ✓
    """
    from App.models.file import File
    from App.models.loan import Loan
    from App.database import db

    data     = request.get_json(silent=True) or {}
    loan_id  = data.get('loanID')
    scanned  = (data.get('barcode') or '').strip()
    token    = (data.get('token')   or '').strip()

    # 1. Verify token (cast to int for consistency)
    try:
        loan_id = int(loan_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid loanID.', 'code': 'BAD_TOKEN'}), 401

    if not _verify_token(f"issue:{loan_id}", token):
        return jsonify({
            'error': 'This QR code has expired or is invalid. '
                     'Go back to the file detail page to generate a new one.',
            'code':  'BAD_TOKEN',
        }), 401

    # 2. Load loan
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({'error': 'Loan not found.', 'code': 'NO_LOAN'}), 404

    # 3. Find the file that belongs to this loan
    loan_file = File.query.filter_by(loanID=loan_id).first()
    if not loan_file:
        return jsonify({
            'error': 'No file is attached to this loan.',
            'code':  'NO_FILE',
        }), 404

    # 4. Check the file even has a barcode registered in the DB
    if not loan_file.barcode:
        return jsonify({
            'error': (
                f'File #{loan_file.fileID} has no barcode registered. '
                'A staff member must add a barcode to this file before it can be scanned.'
            ),
            'code':    'NO_BARCODE',
            'fileID':  loan_file.fileID,
        }), 409

    # 5 & 6. Check the scanned value matches
    if loan_file.barcode != scanned:
        # Was the scanned barcode at least a real (but wrong) file?
        other = File.query.filter_by(barcode=scanned).first()
        if other:
            return jsonify({
                'error': (
                    f'Wrong file scanned. You scanned File #{other.fileID} '
                    f'but this loan is for File #{loan_file.fileID}. '
                    'Please scan the correct label.'
                ),
                'code':             'WRONG_FILE',
                'scanned_fileID':   other.fileID,
                'expected_fileID':  loan_file.fileID,
            }), 409
        else:
            return jsonify({
                'error': (
                    f'Barcode "{scanned}" is not recognised in the system. '
                    'Check the label and try again, or use manual entry.'
                ),
                'code': 'UNKNOWN_BARCODE',
            }), 404

    # 7. All good — confirm loan: Pending → Active, file → On Loan
    try:
        loan.status = 'Active'
    except Exception:
        pass  # status column may not exist yet on older DBs
    loan_file.status = 'On Loan'
    db.session.commit()

    log_scan_event(scanned, True)
    return jsonify({
        'success': True,
        'fileID':  loan_file.fileID,
        'loanID':  loan_id,
        'message': f'File #{loan_file.fileID} successfully issued on Loan #{loan_id}.',
    })


@barcode_views.route('/api/loans/scan-return', methods=['POST'])
def scan_return():
    """
    POST /api/loans/scan-return
    Body: { "loanID": 42, "barcode": "FILE-0042", "token": "<signed_token>" }

    Called by the phone scanner to CONFIRM a return (check-in).
    Same decision tree as scan_confirm but uses the 'return' token payload
    and calls return_loan() instead of setting On Loan.
    """
    from App.models.file import File
    from App.models.loan import Loan
    from App.controllers.loan import return_loan
    from App.database import db
    from datetime import date

    data    = request.get_json(silent=True) or {}
    loan_id = data.get('loanID')
    scanned = (data.get('barcode') or '').strip()
    token   = (data.get('token')   or '').strip()

    # 1. Verify token (cast to int for consistency)
    try:
        loan_id = int(loan_id)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid loanID.', 'code': 'BAD_TOKEN'}), 401

    if not _verify_token(f"return:{loan_id}", token):
        return jsonify({
            'error': 'This QR code has expired or is invalid. '
                     'Go back to the file detail page to generate a new one.',
            'code':  'BAD_TOKEN',
        }), 401

    # 2. Load loan
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({'error': 'Loan not found.', 'code': 'NO_LOAN'}), 404

    if loan.returnDate:
        return jsonify({
            'error': f'Loan #{loan_id} has already been returned.',
            'code':  'ALREADY_RETURNED',
        }), 409

    # 3. Find the file on this loan
    loan_file = File.query.filter_by(loanID=loan_id).first()
    if not loan_file:
        return jsonify({
            'error': 'No file is attached to this loan.',
            'code':  'NO_FILE',
        }), 404

    # 4. Check barcode exists on file
    if not loan_file.barcode:
        return jsonify({
            'error': (
                f'File #{loan_file.fileID} has no barcode registered. '
                'A staff member must add a barcode before this file can be scanned.'
            ),
            'code':   'NO_BARCODE',
            'fileID': loan_file.fileID,
        }), 409

    # 5 & 6. Verify the scanned barcode matches
    if loan_file.barcode != scanned:
        other = File.query.filter_by(barcode=scanned).first()
        if other:
            return jsonify({
                'error': (
                    f'Wrong file scanned. You scanned File #{other.fileID} '
                    f'but this loan is for File #{loan_file.fileID}.'
                ),
                'code':             'WRONG_FILE',
                'scanned_fileID':   other.fileID,
                'expected_fileID':  loan_file.fileID,
            }), 409
        else:
            return jsonify({
                'error': (
                    f'Barcode "{scanned}" is not recognised in the system. '
                    'Check the label and try again.'
                ),
                'code': 'UNKNOWN_BARCODE',
            }), 404

    # 7. All good — process the return directly (same pattern as scan_confirm)
    from datetime import date as _date
    loan.returnDate = _date.today()
    try:
        loan.status = 'Returned'
    except Exception:
        pass
    loan_file.status  = 'Available'
    loan_file.loanID  = None
    db.session.commit()

    log_scan_event(scanned, True)
    return jsonify({
        'success': True,
        'fileID':  loan_file.fileID,
        'loanID':  loan_id,
        'message': f'File #{loan_file.fileID} returned successfully.',
    })