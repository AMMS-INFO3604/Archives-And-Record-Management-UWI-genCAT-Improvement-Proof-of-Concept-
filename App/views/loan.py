# ── Imports ──────────────────────────────────────────────────────────────────
# Flask utilities for building routes, showing messages, redirecting, and
# rendering HTML templates.
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

# jwt_current_user gives us the logged-in user object inside a protected route.
# jwt_required() is a decorator that blocks the route if the user isn't logged in.
from flask_jwt_extended import current_user as jwt_current_user
from flask_jwt_extended import jwt_required

# Loan controller functions — all database logic lives here, not in the views.
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

# Used to look up the StaffUser profile for whoever is currently logged in.
from App.controllers.staffUser import get_staff_user_by_user
from App.controllers.patron import get_all_patrons

from datetime import date, datetime


# ── Blueprint ─────────────────────────────────────────────────────────────────
# A Blueprint groups related routes together. This one owns everything under
# /loans. It's registered in App/views/__init__.py so Flask knows about it.
loan_views = Blueprint('loan_views', __name__, template_folder='../templates')


# ── GET /loans ────────────────────────────────────────────────────────────────
# Main loans listing page. Reads filter/search/pagination params from the URL
# query string, applies them in memory, and renders loans.html.
@loan_views.route('/loans', methods=['GET'])
@jwt_required()
def loans_page():

    # ── Read query-string parameters ──────────────────────────────────────────
    # .strip() removes accidental leading/trailing spaces.
    # .lower() makes all searches case-insensitive.
    search        = request.args.get('search', '').strip().lower()
    type_filter   = request.args.get('type', '')
    date_from     = request.args.get('date_from', '')
    date_to       = request.args.get('date_to', '')
    days_filter   = request.args.get('days', '')
    status_filter = request.args.get('status', 'active')  # active | returned | all
    page          = request.args.get('page', 1, type=int)
    per_page      = 6  # how many loans to show per page

    # ── Base queryset ──────────────────────────────────────────────────────────
    # Start with the right set of loans depending on which status tab is active.
    if status_filter == 'returned':
        loans = get_returned_loans()
    elif status_filter == 'all':
        loans = get_all_loans()
    else:
        # Default tab is 'active' — loans with no returnDate yet.
        loans = get_active_loans()

    # ── Search filter ──────────────────────────────────────────────────────────
    # Only runs if the user typed something in the search box.
    # loan_matches() checks every useful field on the loan and its related
    # records — returning True as soon as any field matches so we stop early.
    if search:
        def loan_matches(l):
            # Match against the loan's own IDs
            if search in str(l.loanID):
                return True
            if search in str(l.patronID):
                return True

            # Match against the patron's username (walks Loan → Patron → User)
            if l.patron and l.patron.user and search in l.patron.user.username.lower():
                return True

            # Match against the staff member's username (walks Loan → StaffUser → User)
            if l.staff_user and l.staff_user.user and search in l.staff_user.user.username.lower():
                return True

            # Match against any file attached to this loan
            for f in l.files:
                if f.fileType and search in f.fileType.lower():
                    return True
                if f.description and search in f.description.lower():
                    return True
                if f.previousDesignation and search in f.previousDesignation.lower():
                    return True
                if search in str(f.fileID):
                    return True

            # Nothing matched
            return False

        loans = [l for l in loans if loan_matches(l)]

    # ── Date range filter ──────────────────────────────────────────────────────
    # Keep only loans whose loanDate falls within the selected range.
    # fromisoformat() converts the 'YYYY-MM-DD' string from the date picker
    # into a Python date object we can compare against.
    if date_from:
        df = date.fromisoformat(date_from)
        loans = [l for l in loans if l.loanDate.date() >= df]
    if date_to:
        dt = date.fromisoformat(date_to)
        loans = [l for l in loans if l.loanDate.date() <= dt]

    # ── Outstanding days filter ────────────────────────────────────────────────
    # Filters active loans by how many days they've been outstanding.
    # '100' is a special case meaning "100 or more days" (the overdue chip).
    # All other values mean "less than N days".
    if days_filter:
        today = date.today()
        days_filter_int = int(days_filter) if days_filter != '100' else None
        filtered = []
        for l in loans:
            # Skip already-returned loans — they have no outstanding days.
            if l.returnDate:
                continue
            diff = (today - l.loanDate.date()).days
            if days_filter == '100' and diff >= 100:
                filtered.append(l)
            elif days_filter_int and diff < days_filter_int:
                filtered.append(l)
        loans = filtered

    # ── Pagination ─────────────────────────────────────────────────────────────
    # Work out total pages, clamp the current page to a valid range, then
    # slice out just the loans for the current page.
    total       = len(loans)
    total_pages = max(1, -(-total // per_page))  # ceiling division
    page        = max(1, min(page, total_pages))  # clamp between 1 and last page
    start       = (page - 1) * per_page
    paginated   = loans[start:start + per_page]

    # ── Render ─────────────────────────────────────────────────────────────────
    # Count active/returned across ALL loans for the stats chips
    all_loans      = get_all_loans()
    active_count   = sum(1 for l in all_loans if not l.returnDate)
    returned_count = sum(1 for l in all_loans if l.returnDate)

    # Pass everything the template needs
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
# Called when a staff member submits the checkout form on the file detail page.
@loan_views.route('/loans', methods=['POST'])
@jwt_required()
def create_loan():

    # Read fileID and patronID from the submitted form.
    # type=int automatically converts the string value to an integer,
    # and returns None if it's missing or not a valid number.
    fileID   = request.form.get('fileID', type=int)
    patronID = request.form.get('patronID', type=int)

    # Both fields are required — bail out early if either is missing.
    if not fileID or not patronID:
        flash('File ID and Patron ID are required.', 'error')
        return redirect(url_for('loan_views.loans_page'))

    # Look up the StaffUser profile for whoever is logged in.
    # jwt_current_user is the User object from the JWT token.
    # We need their StaffUser record to record who processed the loan.
    staff_user = get_staff_user_by_user(jwt_current_user.userID)
    if not staff_user:
        flash('No staff profile found for current user.', 'error')
        return redirect(url_for('loan_views.loans_page'))

    # checkout_files() creates the Loan record and marks the file as 'On Loan'.
    # It expects a list of file IDs so we wrap fileID in a list.
    result = checkout_files([fileID], patronID, staff_user.staffUserID)

    if result:
        flash(f'File #{fileID} successfully loaned to Patron #{patronID}.', 'success')
    else:
        flash(f'Failed to checkout File #{fileID}. It may already be on loan.', 'error')

    # Send the user back to the file's detail page so they can see the updated status.
    return redirect(url_for('file_views.file_detail', fileID=fileID))


# ── GET /loans/<loanID> ────────────────────────────────────────────────────────
# JSON-only endpoint used by the loan detail modal on the loans page.
# When the user clicks "View" on a loan row, the frontend fetches this URL via
# JavaScript and uses the response to populate the modal — no page reload needed.
@loan_views.route('/loans/<int:loanID>', methods=['GET'])
@jwt_required()
def loan_detail_json(loanID):

    loan = get_loan_json(loanID)
    if not loan:
        return jsonify({'error': 'Loan not found'}), 404

    # Attach the list of files to the loan dict before returning.
    loan['files'] = get_loan_files_json(loanID) or []

    response = jsonify(loan)
    response.headers['Content-Type'] = 'application/json'
    return response


# ── POST /loans/<loanID>/return ────────────────────────────────────────────────
# Return route — marks a loan as returned and frees all its files back to
# 'Available'. Also saves any damage/condition notes submitted with the form.
@loan_views.route('/loans/<int:loanID>/return', methods=['POST'])
@jwt_required()
def return_loan_route(loanID):

    loan = get_loan(loanID)
    if not loan:
        flash('Loan not found.', 'error')
        return redirect(url_for('loan_views.loans_page'))

    # Guard against double-returning — the controller is also idempotent but
    # this gives the user a clear message instead of a silent no-op.
    if loan.returnDate:
        flash(f'Loan #{loanID} has already been returned.', 'warning')
        return redirect(url_for('loan_views.loans_page'))

    # ── Read condition notes from the form ─────────────────────────────────────
    # damage_notes is the overall loan-level summary textarea.
    damage_notes = request.form.get('damage_notes', '').strip()

    # Per-file notes are submitted as individual fields named
    # file_condition_<fileID> — one per file attached to the loan.
    # We build a dict {fileID: note} and pass it to the controller.
    file_conditions = {}
    for key, value in request.form.items():
        if key.startswith('file_condition_') and value.strip():
            try:
                file_id = int(key.replace('file_condition_', ''))
                file_conditions[file_id] = value.strip()
            except ValueError:
                # Ignore any malformed field names
                pass

    # ── Call the controller ─────────────────────────────────────────────────────
    # return_loan() sets the returnDate, saves the notes, and marks all
    # attached files back to 'Available'.
    result = return_loan(
        loanID,
        damage_notes=damage_notes if damage_notes else None,
        file_conditions=file_conditions if file_conditions else None,
    )

    # ── Flash result message ────────────────────────────────────────────────────
    # Use 'warning' (amber) when notes were recorded so staff notice they were saved.
    # Use 'success' (green) for a clean return with no damage noted.
    if result:
        if damage_notes or file_conditions:
            flash(
                f'Loan #{loanID} returned with condition notes recorded.',
                'warning'
            )
        else:
            flash(f'Loan #{loanID} has been returned successfully. Files marked as Available.', 'success')
    else:
        flash(f'Failed to return Loan #{loanID}. Please try again.', 'error')

    return redirect(url_for('loan_views.loans_page'))

# ── POST /loans/<loanID>/checkin ───────────────────────────────────────────────
# Check-in route — called from the Check In modal on the file detail page.
# Does the same job as /return but redirects back to the file detail page
# instead of the loans listing, since the user started from there.
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

    # Read the single damage_notes field from the check-in modal textarea.
    # Unlike /return there are no per-file fields here — just one overall note.
    damage_notes = request.form.get('damage_notes', '').strip()

    result = return_loan(
        loanID,
        damage_notes=damage_notes if damage_notes else None,
    )

    # Work out which file to redirect back to — grab it from the loan's files
    # before return_loan() detaches them, or fall back to the loans page.
    file_id = loan.files[0].fileID if loan.files else None

    if result:
        if damage_notes:
            flash(f'File checked in with condition note recorded.', 'warning')
        else:
            flash(f'File checked in successfully and marked as Available.', 'success')
    else:
        flash(f'Failed to check in Loan #{loanID}. Please try again.', 'error')

    # Redirect back to the file detail page the user came from, or the loans
    # listing if we couldn't determine the file ID.
    if file_id:
        return redirect(url_for('file_views.file_detail', fileID=file_id))
    return redirect(url_for('loan_views.loans_page'))

# ── GET /loans/<loanID>/detail ─────────────────────────────────────────────────
# Separate detail page — kept for test compatibility and direct link access.
@loan_views.route('/loans/<int:loanID>/detail', methods=['GET'])
@jwt_required()
def loan_detail_page(loanID):
    loan = get_loan(loanID)
    if not loan:
        flash(f'Loan {loanID} not found.', 'error')
        return redirect(url_for('loan_views.loans_page'))
    return render_template('loan_detail.html', loan=loan)


# ── GET /loaned ────────────────────────────────────────────────────────────────
# Active-checkout dashboard — kept for test compatibility.
@loan_views.route('/loaned', methods=['GET'])
@jwt_required()
def get_loaned_page():
    loans = get_active_loans()
    return render_template('loaned.html', loans=loans, now=datetime.utcnow())


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
    file_ids = data.get('fileIDs')
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
    return jsonify({'message': 'Files checked out successfully', 'loanID': loan.loanID, 'fileCount': len(loan.files)}), 201


@loan_views.route('/api/loans/<int:loanID>/return', methods=['PUT'])
@jwt_required()
def api_return_loan(loanID):
    data = request.json or {}
    loan = return_loan(loanID, returnDate=data.get('returnDate'))
    if not loan:
        return jsonify({'error': 'Loan not found or could not be returned'}), 404
    return jsonify({'message': f'Loan {loanID} returned successfully', 'loanID': loan.loanID, 'returnDate': str(loan.returnDate)}), 200


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