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
    checkout_files,
    create_loan,
    delete_loan,
    get_active_loans,
    get_active_loans_json,
    get_all_loans,
    get_all_loans_json,
    get_loan,
    get_loan_files_json,
    get_loan_json,
    get_loans_by_patron,
    get_loans_by_patron_json,
    get_loans_by_staff,
    get_loans_by_staff_json,
    get_returned_loans,
    get_returned_loans_json,
    return_loan,
    update_loan,
)

loan_views = Blueprint("loan_views", __name__, template_folder="templates")


# ---------------------------------------------------------------------------
# HTML – List
# ---------------------------------------------------------------------------


@loan_views.route("/loans", methods=["GET"])
@jwt_required()
def get_loans_page():
    """Render the loan list page with optional status filter."""
    status_filter = request.args.get("status", "").strip()  # "active" | "returned" | ""
    patron_id = request.args.get("patronID", "").strip()

    if status_filter == "active":
        loans = get_active_loans()
    elif status_filter == "returned":
        loans = get_returned_loans()
    elif patron_id:
        try:
            loans = get_loans_by_patron(int(patron_id))
        except (ValueError, TypeError):
            loans = get_all_loans()
            patron_id = ""
    else:
        loans = get_all_loans()

    return render_template(
        "loans.html",
        loans=loans,
        status_filter=status_filter,
        patron_id=patron_id,
    )


# ---------------------------------------------------------------------------
# HTML – Detail
# ---------------------------------------------------------------------------


@loan_views.route("/loans/<int:loanID>/detail", methods=["GET"])
@jwt_required()
def loan_detail_page(loanID):
    """Render the detail page for a single loan."""
    loan = get_loan(loanID)
    if not loan:
        flash(f"Loan {loanID} not found.", "error")
        return redirect(url_for("loan_views.get_loans_page"))
    return render_template("loan_detail.html", loan=loan)


# ---------------------------------------------------------------------------
# API – Read (all)
# ---------------------------------------------------------------------------


@loan_views.route("/api/loans", methods=["GET"])
@jwt_required()
def api_get_all_loans():
    """Return all loans as JSON."""
    loans = get_all_loans_json()
    if not loans:
        return jsonify({"message": "No loans found"}), 404
    return jsonify(loans), 200


@loan_views.route("/api/loans/active", methods=["GET"])
@jwt_required()
def api_get_active_loans():
    """Return all active (not yet returned) loans as JSON."""
    loans = get_active_loans_json()
    if not loans:
        return jsonify({"message": "No active loans found"}), 404
    return jsonify(loans), 200


@loan_views.route("/api/loans/returned", methods=["GET"])
@jwt_required()
def api_get_returned_loans():
    """Return all returned loans as JSON."""
    loans = get_returned_loans_json()
    if not loans:
        return jsonify({"message": "No returned loans found"}), 404
    return jsonify(loans), 200


# ---------------------------------------------------------------------------
# API – Read (single)
# ---------------------------------------------------------------------------


@loan_views.route("/api/loans/<int:loanID>", methods=["GET"])
@jwt_required()
def api_get_loan(loanID):
    """Return a single loan as JSON."""
    loan = get_loan_json(loanID)
    if not loan:
        return jsonify({"error": "Loan not found"}), 404
    return jsonify(loan), 200


@loan_views.route("/api/loans/<int:loanID>/files", methods=["GET"])
@jwt_required()
def api_get_loan_files(loanID):
    """Return all files currently attached to a loan."""
    files = get_loan_files_json(loanID)
    if files is None:
        return jsonify({"error": "Loan not found"}), 404
    if not files:
        return jsonify({"message": "No files attached to this loan"}), 200
    return jsonify(files), 200


# ---------------------------------------------------------------------------
# API – Read (by patron / staff)
# ---------------------------------------------------------------------------


@loan_views.route("/api/loans/patron/<int:patronID>", methods=["GET"])
@jwt_required()
def api_get_loans_by_patron(patronID):
    """Return all loans for a given patron as JSON."""
    loans = get_loans_by_patron_json(patronID)
    if not loans:
        return jsonify({"message": f"No loans found for patron {patronID}"}), 404
    return jsonify(loans), 200


@loan_views.route("/api/loans/staff/<int:staffUserID>", methods=["GET"])
@jwt_required()
def api_get_loans_by_staff(staffUserID):
    """Return all loans processed by a given staff user as JSON."""
    loans = get_loans_by_staff_json(staffUserID)
    if not loans:
        return jsonify({"message": f"No loans found for staff user {staffUserID}"}), 404
    return jsonify(loans), 200


# ---------------------------------------------------------------------------
# API – Create / Checkout
# ---------------------------------------------------------------------------


@loan_views.route("/api/loans", methods=["POST"])
@jwt_required()
def api_create_loan():
    """Create a bare loan record (no files attached).

    Expected JSON body:
        { "patronID": 1, "processedByStaffUserID": 2, "loanDate": "2025-01-15" }
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    patron_id = data.get("patronID")
    if not patron_id:
        return jsonify({"error": "patronID is required"}), 400

    loan = create_loan(
        patronID=patron_id,
        processedByStaffUserID=data.get("processedByStaffUserID"),
        loanDate=data.get("loanDate"),
    )
    if not loan:
        return jsonify(
            {"error": "Failed to create loan – check patronID and staffUserID"}
        ), 400

    return jsonify({"message": "Loan created successfully", "loanID": loan.loanID}), 201


@loan_views.route("/api/loans/checkout", methods=["POST"])
@jwt_required()
def api_checkout_files():
    """Create a loan and immediately attach a list of files to it.

    Expected JSON body:
        {
            "patronID": 1,
            "fileIDs": [3, 7, 12],
            "processedByStaffUserID": 2
        }

    All specified files must currently have status "Available".
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    patron_id = data.get("patronID")
    file_ids = data.get("fileIDs")

    if not patron_id:
        return jsonify({"error": "patronID is required"}), 400
    if not file_ids or not isinstance(file_ids, list):
        return jsonify({"error": "fileIDs must be a non-empty list"}), 400

    loan = checkout_files(
        patronID=patron_id,
        file_ids=file_ids,
        processedByStaffUserID=data.get("processedByStaffUserID"),
    )
    if not loan:
        return jsonify(
            {
                "error": "Checkout failed – verify patronID and that all files are Available"
            }
        ), 400

    return jsonify(
        {
            "message": "Files checked out successfully",
            "loanID": loan.loanID,
            "fileCount": len(loan.files),
        }
    ), 201


# ---------------------------------------------------------------------------
# API – Return
# ---------------------------------------------------------------------------


@loan_views.route("/api/loans/<int:loanID>/return", methods=["PUT"])
@jwt_required()
def api_return_loan(loanID):
    """Mark a loan as returned and set all its files back to Available.

    Optional JSON body:
        { "returnDate": "2025-02-01T10:30:00" }
    """
    data = request.json or {}
    loan = return_loan(loanID, returnDate=data.get("returnDate"))
    if not loan:
        return jsonify({"error": "Loan not found or could not be returned"}), 404

    return jsonify(
        {
            "message": f"Loan {loanID} returned successfully",
            "loanID": loan.loanID,
            "returnDate": str(loan.returnDate),
        }
    ), 200


# ---------------------------------------------------------------------------
# API – Update
# ---------------------------------------------------------------------------


@loan_views.route("/api/loans/<int:loanID>", methods=["PUT"])
@jwt_required()
def api_update_loan(loanID):
    """Update mutable fields on an existing loan.

    Accepted JSON fields (all optional):
        patronID, processedByStaffUserID, loanDate, returnDate
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    loan = update_loan(
        loanID=loanID,
        patronID=data.get("patronID"),
        processedByStaffUserID=data.get("processedByStaffUserID"),
        loanDate=data.get("loanDate"),
        returnDate=data.get("returnDate"),
    )
    if not loan:
        return jsonify({"error": "Loan not found or update failed"}), 404

    return jsonify(
        {"message": f"Loan {loanID} updated successfully", "loanID": loan.loanID}
    ), 200


# ---------------------------------------------------------------------------
# API – Delete
# ---------------------------------------------------------------------------


@loan_views.route("/api/loans/<int:loanID>", methods=["DELETE"])
@jwt_required()
def api_delete_loan(loanID):
    """Delete a loan record.  Attached files are detached and set back to Available."""
    result = delete_loan(loanID)
    if not result:
        return jsonify({"error": "Loan not found"}), 404

    return jsonify({"message": f"Loan {loanID} deleted successfully"}), 200
