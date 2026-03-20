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
    get_active_loans,
    get_returned_loans,
    return_loan,
    create_loan,
    get_loan
)
from App.controllers.staffUser import get_staff_user_by_user
from datetime import date, datetime

loan_views = Blueprint('loan_views', __name__, template_folder='../templates')

@loan_views.route('/loans', methods=['GET'])
@jwt_required()
def get_loans_page():
    search_query = request.args.get('search', '').strip().lower()
    status = request.args.get('status', 'Active') # Active | Returned | All
    
    if status == 'Returned':
        loans = get_returned_loans()
    elif status == 'All':
        loans = get_all_loans()
    else:
        loans = get_active_loans()

    if search_query:
        # Simple in-memory search for now to match template expectations
        filtered = []
        for l in loans:
            if search_query in str(l.loanID).lower(): filtered.append(l)
            elif l.patron and l.patron.user and search_query in l.patron.user.username.lower(): filtered.append(l)
            elif search_query in str(l.patronID).lower(): filtered.append(l)
            elif any(search_query in (f.description or '').lower() for f in l.files): filtered.append(l)
            elif any(search_query in str(f.fileID).lower() for f in l.files): filtered.append(l)
        loans = filtered

    return render_template(
        "loans.html",
        loans=loans,
        status=status,
        search_query=search_query
    )

@loan_views.route('/loans/create', methods=['POST'])
@jwt_required()
def create_loan_action():
    fileID = request.form.get('fileID')
    patronID = request.form.get('patronID')
    due_date_str = request.form.get('dueDate')
    
    if not fileID or not patronID:
        flash("File and Patron are required.", "error")
        return redirect(request.referrer or url_for('loan_views.get_loans_page'))
    
    # Get the current staff user's ID
    staff_user = get_staff_user_by_user(jwt_current_user.userID)
    
    try:
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        loan = create_loan(
            fileID=fileID,
            patronID=patronID,
            processedByStaffUserID=staff_user.staffUserID if staff_user else None,
            dueDate=due_date
        )
        if loan:
            flash(f"Loan created successfully for file {fileID}.", "success")
        else:
            flash("Failed to create loan. File might not be available.", "error")
    except Exception as e:
        flash(f"Error creating loan: {str(e)}", "error")
        
    return redirect(request.referrer or url_for('loan_views.get_loans_page'))

@loan_views.route('/loans/<int:loan_id>/return', methods=['POST'])
@jwt_required()
def return_loan_action(loan_id):
    loan = return_loan(loan_id)
    if loan:
        flash(f"Loan {loan_id} returned successfully.", "success")
    else:
        flash(f"Failed to return loan {loan_id}.", "error")
    return redirect(request.referrer or url_for('loan_views.get_loans_page'))

@loan_views.route('/loans/<int:loan_id>/detail', methods=['GET'])
@jwt_required()
def get_loan_details_page(loan_id):
    loan = get_loan(loan_id)
    if not loan:
        flash("Loan not found.", "error")
        return redirect(url_for('loan_views.get_loans_page'))
    return render_template("message.html", title="Loan Details", message=f"Details for loan {loan_id} - Feature coming soon.")
