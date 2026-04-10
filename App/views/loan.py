# ── Imports ──────────────────────────────────────────────────────────────────
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

from App.controllers.loan import (
    get_all_loans,
    get_all_loans_json,
    get_loan,
    get_loan_json,
    get_loan_files_json,
    get_active_loans,
    get_active_loans_json,
    get_returned_loans,
    get_returned_loans_json,
    get_loans_by_patron,
    get_loans_by_patron_json,
    get_loans_by_staff,
    get_loans_by_staff_json,
    return_loan,
    checkout_files,
    create_loan,
    delete_loan,
    update_loan,
)

from App.controllers.staffUser import get_staff_user_by_user
from App.controllers.patron import get_all_patrons

from datetime import date, datetime
from App.database import db

from App.models.file import File
from App.models.loan import Loan

# ── Blueprint ─────────────────────────────────────────────────────────────────
loan_views = Blueprint('loan_views', __name__, template_folder='../templates')




# ── POST /loans/<loanID>/cancel ───────────────────────────────────────────────
@loan_views.route('/loans/<int:loanID>/cancel', methods=['POST'])
@jwt_required()
def cancel_pending_loan(loanID):
    """Cancel a Pending loan that was never confirmed by scan.
    Detaches the file and deletes the loan record."""
    loan = get_loan(loanID)
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404

    if getattr(loan, 'status', None) != 'Pending':
        return jsonify({'error': 'Only Pending loans can be cancelled this way'}), 409

    # Detach files and delete the loan
    for f in loan.files:
        f.loanID = None
        f.status = 'Available'
    db.session.delete(loan)
    db.session.commit()
    print(f"[cancel_pending_loan] Loan #{loanID} cancelled and deleted.")
    return jsonify({'message': f'Loan #{loanID} cancelled.'}), 200

# ── GET /loans ────────────────────────────────────────────────────────────────
@loan_views.route('/loans', methods=['GET'])
@jwt_required()
def loans_page():

    search        = request.args.get('search', '').strip().lower()
    type_filter   = request.args.get('type', '')
    date_from     = request.args.get('date_from', '')
    date_to       = request.args.get('date_to', '')
    days_filter   = request.args.get('days', '')
    status_filter = request.args.get('status', 'active')
    page          = request.args.get('page', 1, type=int)
    per_page      = 6

    if status_filter == 'returned':
        loans = get_returned_loans()
    elif status_filter == 'all':
        loans = get_all_loans()
    else:
        loans = get_active_loans()

    if search:
        def loan_matches(l):
            if search in str(l.loanID):
                return True
            if search in str(l.patronID):
                return True
            if l.patron and l.patron.user and search in l.patron.user.username.lower():
                return True
            if l.staff_user and l.staff_user.user and search in l.staff_user.user.username.lower():
                return True
            for f in l.files:
                if f.fileType and search in f.fileType.lower():
                    return True
                if f.description and search in f.description.lower():
                    return True
                if f.previousDesignation and search in f.previousDesignation.lower():
                    return True
                if search in str(f.fileID):
                    return True
            return False

        loans = [l for l in loans if loan_matches(l)]

    if date_from:
        df = date.fromisoformat(date_from)
        loans = [l for l in loans if l.loanDate.date() >= df]
    if date_to:
        dt = date.fromisoformat(date_to)
        loans = [l for l in loans if l.loanDate.date() <= dt]

    if days_filter:
        today = date.today()
        days_filter_int = int(days_filter) if days_filter != '100' else None
        filtered = []
        for l in loans:
            if l.returnDate:
                continue
            diff = (today - l.loanDate.date()).days
            if days_filter == '100' and diff >= 100:
                filtered.append(l)
            elif days_filter_int and diff < days_filter_int:
                filtered.append(l)
        loans = filtered

    total       = len(loans)
    total_pages = max(1, -(-total // per_page))
    page        = max(1, min(page, total_pages))
    start       = (page - 1) * per_page
    paginated   = loans[start:start + per_page]

    all_loans      = get_all_loans()
    active_count   = sum(1 for l in all_loans if not l.returnDate)
    returned_count = sum(1 for l in all_loans if l.returnDate)

    return render_template('loans.html',
        loans          = paginated,
        total          = total,
        page           = page,
        total_pages    = total_pages,
        per_page       = per_page,
        search         = search,
        type_filter    = type_filter,
        date_from      = date_from,
        date_to        = date_to,
        days_filter    = days_filter,
        status_filter  = status_filter,
        today          = date.today(),
        active_count   = active_count,
        returned_count = returned_count,
    )


# ── POST /loans ────────────────────────────────────────────────────────────────
# Checkout route — creates a new loan for a single file.
# Now detects AJAX / fetch calls and returns JSON instead of redirecting,
# so file_detail.html can read the new loanID and display the QR code.
@loan_views.route('/loans', methods=['POST'])
@jwt_required()
def create_loan_view():

    # ── Detect whether caller wants JSON ──────────────────────────────────────
    # fetch() from file_detail.html sends X-Requested-With so we can
    # tell it apart from a plain form submit.
    wants_json = (
        request.is_json
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in request.headers.get('Accept', '')
    )

    # ── Read form values ──────────────────────────────────────────────────────
    fileID_raw   = request.form.get('fileID')
    patronID_raw = request.form.get('patronID')

    print(f"[POST /loans] Raw form values → fileID={fileID_raw!r}, patronID={patronID_raw!r}")

    try:
        fileID   = int(fileID_raw)   if fileID_raw   else None
        patronID = int(patronID_raw) if patronID_raw else None
    except (ValueError, TypeError):
        fileID   = None
        patronID = None

    print(f"[POST /loans] Parsed → fileID={fileID}, patronID={patronID}")

    if not fileID or not patronID:
        if wants_json:
            return jsonify({'error': 'File ID and Patron ID are required.'}), 400
        flash('File ID and Patron ID are required.', 'error')
        return redirect(url_for('file_views.file_detail_page', fileID=fileID or 0))

    # ── Get current staff ─────────────────────────────────────────────────────
    staff_user = get_staff_user_by_user(jwt_current_user.userID)
    if not staff_user:
        if wants_json:
            return jsonify({'error': 'No staff profile found for current user.'}), 403
        flash('No staff profile found for current user.', 'error')
        return redirect(url_for('file_views.file_detail_page', fileID=fileID))

    print(f"[POST /loans] Processing as staffUserID={staff_user.staffUserID}")

    # ── Validate file is available ───────────────────────────────────────────
    file = db.session.get(File, fileID)
    if not file:
        msg = f'File #{fileID} not found.'
        if wants_json: return jsonify({'error': msg}), 404
        flash(msg, 'error')
        return redirect(url_for('file_views.file_detail_page', fileID=fileID))

    if file.status != 'Available':
        msg = f'File #{fileID} is not available (status: {file.status}).'
        if wants_json: return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('file_views.file_detail_page', fileID=fileID))

    # ── Create a PENDING loan — file stays Available until scan confirms ──────
    loan = create_loan(
        patronID=patronID,
        processedByStaffUserID=staff_user.staffUserID,
    )
    if not loan:
        msg = 'Failed to create loan record.'
        if wants_json: return jsonify({'error': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('file_views.file_detail_page', fileID=fileID))

    # Mark loan as Pending and link the file (but don't change file status yet)
    loan.status = 'Pending'
    file.loanID = loan.loanID
    db.session.commit()

    print(f"[POST /loans] Pending loan #{loan.loanID} created for File #{fileID}")

    if wants_json:
        return jsonify({
            'loanID':  loan.loanID,
            'fileID':  fileID,
            'status':  'Pending',
            'message': f'Pending loan #{loan.loanID} created. Scan barcode to confirm.',
        }), 201

    # Non-AJAX: go straight to QR page (no scan required path)
    flash(f'Loan #{loan.loanID} created. Scan the barcode to confirm issue.', 'success')
    return redirect(url_for('file_views.file_detail_page', fileID=fileID))


# ── GET /loans/<loanID> ────────────────────────────────────────────────────────
@loan_views.route('/loans/<int:loanID>', methods=['GET'])
@jwt_required()
def loan_detail_json(loanID):
    loan = get_loan_json(loanID)
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404

    loan['files'] = get_loan_files_json(loanID) or []

    # Include live loan status for the QR poller — derive from the ORM object
    # so we always get the freshest value from DB
    loan_obj = get_loan(loanID)
    raw_status  = getattr(loan_obj, 'status', None)
    return_date = getattr(loan_obj, 'returnDate', None)

    # If returnDate is set the loan is effectively Returned regardless of status col
    if return_date:
        loan['loanStatus']  = 'Returned'
        loan['returnDate']  = str(return_date)
    else:
        loan['loanStatus']  = raw_status or 'Active'
        loan['returnDate']  = None

    # Patron username (walks Loan → Patron → User → username)
    loan['patronUsername'] = (
        loan_obj.patron.user.username
        if loan_obj and loan_obj.patron and loan_obj.patron.user
        else None
    )

    # Due date — stored as dueDate on the loan if present, else fall back to loanDate + 30 days
    from datetime import timedelta
    due_raw = getattr(loan_obj, 'dueDate', None)
    if due_raw:
        loan['dueDate'] = str(due_raw)
    elif loan_obj and loan_obj.loanDate:
        loan['dueDate'] = str((loan_obj.loanDate + timedelta(days=30)).date())
    else:
        loan['dueDate'] = None

    response = jsonify(loan)
    response.headers['Content-Type'] = 'application/json'
    return response


# ── POST /loans/<loanID>/return ────────────────────────────────────────────────
@loan_views.route('/loans/<int:loanID>/return', methods=['POST'])
@jwt_required()
def return_loan_route(loanID):

    loan = get_loan(loanID)
    if not loan:
        flash('Loan not found.', 'error')
        return redirect(url_for('loan_views.loans_page'))

    if loan.returnDate:
        flash(f'Loan #{loanID} has already been returned.', 'warning')
        return redirect(url_for('loan_views.loans_page'))

    damage_notes = request.form.get('damage_notes', '').strip()

    file_conditions = {}
    for key, value in request.form.items():
        if key.startswith('file_condition_') and value.strip():
            try:
                file_id = int(key.replace('file_condition_', ''))
                file_conditions[file_id] = value.strip()
            except ValueError:
                pass

    result = return_loan(
        loanID,
        damage_notes=damage_notes if damage_notes else None,
        file_conditions=file_conditions if file_conditions else None,
    )

    if result:
        if damage_notes or file_conditions:
            flash(f'Loan #{loanID} returned with condition notes recorded.', 'warning')
        else:
            flash(f'Loan #{loanID} has been returned successfully. Files marked as Available.', 'success')
    else:
        flash(f'Failed to return Loan #{loanID}. Please try again.', 'error')

    return redirect(url_for('loan_views.loans_page'))


# ── POST /loans/<loanID>/checkin ───────────────────────────────────────────────
@loan_views.route('/loans/<int:loanID>/checkin', methods=['POST'])
@jwt_required()
def checkin_loan_route(loanID):

    loan = get_loan(loanID)
    if not loan:
        flash('Loan not found.', 'error')
        return redirect(url_for('loan_views.loans_page'))

    if loan.returnDate:
        flash(f'Loan #{loanID} has already been returned.', 'warning')
        return redirect(url_for('loan_views.loans_page'))

    damage_notes = request.form.get('damage_notes', '').strip()

    # Capture file IDs BEFORE return_loan() sets file.loanID = NULL.
    # After check-in, loan.files is empty so we cannot read them afterwards.
    file_ids = [f.fileID for f in loan.files]

    result = return_loan(
        loanID,
        damage_notes=damage_notes if damage_notes else None,
    )

    file_id = file_ids[0] if file_ids else None

    if result:
        if damage_notes:
            flash(f'File checked in with condition note recorded.', 'warning')
        else:
            flash(f'File checked in successfully and marked as Available.', 'success')
    else:
        flash(f'Failed to check in Loan #{loanID}. Please try again.', 'error')

    if file_id:
        # Pass loanID as last_loan_id so file_detail_page can show the
        # returned loan in history and display its damage notes, even though
        # file.loanID has just been cleared to NULL by return_loan().
        return redirect(url_for('file_views.file_detail_page',
                                fileID=file_id, last_loan_id=loanID))
    return redirect(url_for('loan_views.loans_page'))


# ── GET /loans/<loanID>/detail ─────────────────────────────────────────────────
@loan_views.route('/loans/<int:loanID>/detail', methods=['GET'])
@jwt_required()
def loan_detail_page(loanID):
    loan = get_loan(loanID)
    if not loan:
        flash(f'Loan {loanID} not found.', 'error')
        return redirect(url_for('loan_views.loans_page'))
    all_loans      = get_all_loans()
    active_count   = sum(1 for l in all_loans if not l.returnDate)
    returned_count = sum(1 for l in all_loans if l.returnDate)
    loans          = get_active_loans()
    return render_template('loans.html',
        loans=loans, total=len(loans), page=1, total_pages=1,
        per_page=len(loans) or 1, search='', type_filter='',
        date_from='', date_to='', days_filter='', status_filter='active',
        today=date.today(), active_count=active_count,
        returned_count=returned_count,
    )


# ── GET /loaned ────────────────────────────────────────────────────────────────
@loan_views.route('/loaned', methods=['GET'])
@jwt_required()
def get_loaned_page():
    all_loans      = get_all_loans()
    active_count   = sum(1 for l in all_loans if not l.returnDate)
    returned_count = sum(1 for l in all_loans if l.returnDate)
    loans          = get_active_loans()
    return render_template('loans.html',
        loans=loans, total=len(loans), page=1, total_pages=1,
        per_page=len(loans) or 1, search='', type_filter='',
        date_from='', date_to='', days_filter='', status_filter='active',
        today=date.today(), active_count=active_count,
        returned_count=returned_count,
    )


# ── API routes ─────────────────────────────────────────────────────────────────

@loan_views.route('/api/loans', methods=['GET'])
@jwt_required()
def api_get_all_loans():
    loans = get_all_loans_json()
    if not loans:
        return jsonify({'message': 'No loans found'}), 404
    return jsonify(loans), 200


@loan_views.route('/api/loans/active', methods=['GET'])
@jwt_required()
def api_get_active_loans():
    loans = get_active_loans_json()
    if not loans:
        return jsonify({'message': 'No active loans found'}), 404
    return jsonify(loans), 200


@loan_views.route('/api/loans/returned', methods=['GET'])
@jwt_required()
def api_get_returned_loans():
    loans = get_returned_loans_json()
    if not loans:
        return jsonify({'message': 'No returned loans found'}), 404
    return jsonify(loans), 200


@loan_views.route('/api/loans/patron/<int:patronID>', methods=['GET'])
@jwt_required()
def api_get_loans_by_patron(patronID):
    loans = get_loans_by_patron_json(patronID)
    if not loans:
        return jsonify({'message': f'No loans found for patron {patronID}'}), 404
    return jsonify(loans), 200


@loan_views.route('/api/loans/staff/<int:staffUserID>', methods=['GET'])
@jwt_required()
def api_get_loans_by_staff(staffUserID):
    loans = get_loans_by_staff_json(staffUserID)
    if not loans:
        return jsonify({'message': f'No loans found for staff user {staffUserID}'}), 404
    return jsonify(loans), 200


@loan_views.route('/api/loans/<int:loanID>', methods=['GET'])
@jwt_required()
def api_get_loan(loanID):
    loan = get_loan_json(loanID)
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404
    return jsonify(loan), 200


@loan_views.route('/api/loans/<int:loanID>/files', methods=['GET'])
@jwt_required()
def api_get_loan_files(loanID):
    files = get_loan_files_json(loanID)
    if files is None:
        return jsonify({'error': 'Loan not found'}), 404
    if not files:
        return jsonify({'message': 'No files attached to this loan'}), 200
    return jsonify(files), 200


@loan_views.route('/api/loans', methods=['POST'])
@jwt_required()
def api_create_loan():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    patron_id = data.get('patronID')
    if not patron_id:
        return jsonify({'error': 'patronID is required'}), 400
    loan = create_loan(
        patronID=patron_id,
        processedByStaffUserID=data.get('processedByStaffUserID'),
        loanDate=data.get('loanDate'),
    )
    if not loan:
        return jsonify({'error': 'Failed to create loan – check patronID and staffUserID'}), 400
    return jsonify({'message': 'Loan created successfully', 'loanID': loan.loanID}), 201


@loan_views.route('/api/loans/checkout', methods=['POST'])
@jwt_required()
def api_checkout_files():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    patron_id = data.get('patronID')
    file_ids  = data.get('fileIDs')
    if not patron_id:
        return jsonify({'error': 'patronID is required'}), 400
    if not file_ids or not isinstance(file_ids, list):
        return jsonify({'error': 'fileIDs must be a non-empty list'}), 400
    loan = checkout_files(
        patronID=patron_id,
        file_ids=file_ids,
        processedByStaffUserID=data.get('processedByStaffUserID'),
    )
    if not loan:
        return jsonify({'error': 'Checkout failed – verify patronID and that all files are Available'}), 400
    return jsonify({
        'message':   'Files checked out successfully',
        'loanID':    loan.loanID,
        'fileCount': len(loan.files),
    }), 201


@loan_views.route('/api/loans/<int:loanID>/return', methods=['PUT'])
@jwt_required()
def api_return_loan(loanID):
    data = request.json or {}
    loan = return_loan(loanID, returnDate=data.get('returnDate'))
    if not loan:
        return jsonify({'error': 'Loan not found or could not be returned'}), 404
    return jsonify({
        'message':    f'Loan {loanID} returned successfully',
        'loanID':     loan.loanID,
        'returnDate': str(loan.returnDate),
    }), 200


@loan_views.route('/api/loans/<int:loanID>', methods=['PUT'])
@jwt_required()
def api_update_loan(loanID):
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    loan = update_loan(
        loanID=loanID,
        patronID=data.get('patronID'),
        processedByStaffUserID=data.get('processedByStaffUserID'),
        loanDate=data.get('loanDate'),
        returnDate=data.get('returnDate'),
    )
    if not loan:
        return jsonify({'error': 'Loan not found or update failed'}), 404
    return jsonify({'message': f'Loan {loanID} updated successfully', 'loanID': loan.loanID}), 200


@loan_views.route('/api/loans/<int:loanID>', methods=['DELETE'])
@jwt_required()
def api_delete_loan(loanID):
    result = delete_loan(loanID)
    if not result:
        return jsonify({'error': 'Loan not found'}), 404
    return jsonify({'message': f'Loan {loanID} deleted successfully'}), 200