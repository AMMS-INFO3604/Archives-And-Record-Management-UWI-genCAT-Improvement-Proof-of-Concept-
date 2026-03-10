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
# HTML – Create (form POST)
# ---------------------------------------------------------------------------


@loan_views.route("/loans", methods=["POST"])
@jwt_required()
def create_loan_page():
    """Handle the loan creation form submitted from the loans list page.

    Expected form fields:
        patronID              (required)  – integer patron ID
        processedByStaffUserID (optional) – integer staff user ID
        fileIDs               (optional)  – comma-separated file IDs to check
                                            out immediately (e.g. "1,3,7")
    """
    patron_id_raw = request.form.get("patronID", "").strip()
    staff_id_raw = request.form.get("processedByStaffUserID", "").strip()
    file_ids_raw = request.form.get("fileIDs", "").strip()

    # --- Validate patronID ---------------------------------------------------
    if not patron_id_raw:
        flash("Patron ID is required to create a loan.", "error")
        return redirect(url_for("loan_views.get_loans_page"))

    try:
        patron_id = int(patron_id_raw)
    except ValueError:
        flash("Patron ID must be a whole number.", "error")
        return redirect(url_for("loan_views.get_loans_page"))

    # --- Parse optional staff ID --------------------------------------------
    processed_by = None
    if staff_id_raw:
        try:
            processed_by = int(staff_id_raw)
        except ValueError:
            flash("Staff User ID must be a whole number.", "error")
            return redirect(url_for("loan_views.get_loans_page"))

    # --- Parse optional file IDs and route to the right controller ----------
    if file_ids_raw:
        raw_parts = [p.strip() for p in file_ids_raw.split(",") if p.strip()]
        try:
            file_ids = [int(p) for p in raw_parts]
        except ValueError:
            flash(
                "File IDs must be comma-separated whole numbers (e.g. 1,3,7).", "error"
            )
            return redirect(url_for("loan_views.get_loans_page"))

        loan = checkout_files(
            patronID=patron_id,
            file_ids=file_ids,
            processedByStaffUserID=processed_by,
        )
        if not loan:
            flash(
                "Checkout failed. Check that the patron exists, all file IDs are "
                "valid, and every file has status 'Available'.",
                "error",
            )
            return redirect(url_for("loan_views.get_loans_page"))

        flash(
            f"Loan #{loan.loanID} created – "
            f"{len(loan.files)} file{'s' if len(loan.files) != 1 else ''} checked out.",
            "success",
        )
    else:
        loan = create_loan(
            patronID=patron_id,
            processedByStaffUserID=processed_by,
        )
        if not loan:
            flash(
                "Failed to create loan. Check that the patron ID (and staff ID, "
                "if provided) are valid.",
                "error",
            )
            return redirect(url_for("loan_views.get_loans_page"))

        flash(f"Loan #{loan.loanID} created successfully.", "success")

    return redirect(url_for("loan_views.loan_detail_page", loanID=loan.loanID))


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
# HTML – Check-in (form POST)
# ---------------------------------------------------------------------------


@loan_views.route("/loans/<int:loanID>/checkin", methods=["POST"])
@jwt_required()
def checkin_loan_page(loanID):
    """Mark an active loan as returned via an HTML form submission.

    No form fields are required – the action is triggered by submitting the
    form for the given loanID.  An optional ``returnDate`` field (ISO-8601
    string, e.g. ``2025-06-15``) can be included to override the default of
    'now'.  On success every file attached to the loan is set back to
    'Available' and its loanID is cleared.

    Expected form fields:
        returnDate  (optional) – ISO-8601 date/datetime string
    """
    loan = get_loan(loanID)
    if not loan:
        flash(f"Loan #{loanID} not found.", "error")
        return redirect(url_for("loan_views.get_loans_page"))

    if loan.returnDate is not None:
        flash(
            f"Loan #{loanID} has already been returned on "
            f"{loan.returnDate.strftime('%d %b %Y')}.",
            "warning",
        )
        return redirect(url_for("loan_views.loan_detail_page", loanID=loanID))

    # Parse optional override return date
    return_date = None
    return_date_raw = request.form.get("returnDate", "").strip()
    if return_date_raw:
        from datetime import datetime as dt

        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                return_date = dt.strptime(return_date_raw, fmt)
                break
            except ValueError:
                continue
        if return_date is None:
            flash(
                "Invalid return date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM.",
                "error",
            )
            return redirect(url_for("loan_views.loan_detail_page", loanID=loanID))

    updated = return_loan(loanID, returnDate=return_date)
    if not updated:
        flash(f"Failed to check in loan #{loanID}. Please try again.", "error")
        return redirect(url_for("loan_views.loan_detail_page", loanID=loanID))

    file_count = 0 if updated.files is None else len(updated.files)
    flash(
        f"Loan #{loanID} checked in successfully – "
        f"{file_count} file{'s' if file_count != 1 else ''} returned to 'Available'.",
        "success",
    )
    return redirect(url_for("loan_views.loan_detail_page", loanID=loanID))


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
