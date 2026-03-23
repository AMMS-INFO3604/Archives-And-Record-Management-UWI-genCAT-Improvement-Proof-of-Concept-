from datetime import datetime

from App.database import db
from App.models.file import File
from App.models.loan import Loan
from App.models.patron import Patron
from App.models.staff_user import StaffUser

# ---------------------------------------------------------------------------
# Create / Checkout
# ---------------------------------------------------------------------------


def create_loan(patronID, processedByStaffUserID=None, loanDate=None):
    """Create a new Loan record for a given patron.

    Args:
        patronID: The ID of the Patron taking out the loan.
        processedByStaffUserID: Optional ID of the StaffUser processing it.
        loanDate: Optional datetime for the loan; defaults to now.

    Returns:
        The new Loan instance, or None on failure.
    """
    patron = db.session.get(Patron, patronID)
    if not patron:
        print(f"Patron with ID {patronID} not found.")
        return None

    if processedByStaffUserID is not None:
        staff = db.session.get(StaffUser, processedByStaffUserID)
        if not staff:
            print(f"StaffUser with ID {processedByStaffUserID} not found.")
            return None

    loan = Loan(
        patronID=patronID,
        processedByStaffUserID=processedByStaffUserID,
        loanDate=loanDate or datetime.utcnow(),
    )
    try:
        db.session.add(loan)
        db.session.commit()
        return loan
    except Exception as e:
        db.session.rollback()
        print(f"Error creating loan: {e}")
        return None


def checkout_files(patronID, file_ids, processedByStaffUserID=None):
    print(f"[checkout_files] START - patron={patronID}, files={file_ids}, staff={processedByStaffUserID}")

    if not file_ids:
        print("[checkout_files] ERROR: No file_ids provided")
        return None

    loan = create_loan(patronID, processedByStaffUserID=processedByStaffUserID)
    if not loan:
        print("[checkout_files] ERROR: Failed to create loan")
        return None

    errors = []
    updated_files = []

    for file_id in file_ids:
        # Fresh query + lock to avoid stale data
        file = db.session.query(File).filter(File.fileID == file_id).with_for_update().first()

        if not file:
            errors.append(f"File {file_id} not found")
            continue

        print(f"[checkout_files] File {file_id}: status='{file.status}', loanID={file.loanID}")

        if file.status != "Available":
            errors.append(f"File {file_id} not available (status: {file.status})")
            continue

        # Attach
        file.loanID = loan.loanID
        file.status = "On Loan"
        updated_files.append(file.fileID)

    if errors:
        print(f"[checkout_files] ERRORS: {errors}")
        db.session.rollback()
        return None

    try:
        db.session.commit()
        print(f"[checkout_files] SUCCESS - Loan {loan.loanID} created, files updated: {updated_files}")
        return loan
    except Exception as e:
        db.session.rollback()
        print(f"[checkout_files] COMMIT FAILED: {str(e)}")
        return None

# ---------------------------------------------------------------------------
# Read – single record
# ---------------------------------------------------------------------------


def get_loan(loanID):
    """Return a Loan by its primary key."""
    return db.session.get(Loan, loanID)


def get_loan_json(loanID):
    loan = get_loan(loanID)
    if not loan:
        return None
    return _loan_to_dict(loan)


# ---------------------------------------------------------------------------
# Read – all records
# ---------------------------------------------------------------------------


def get_all_loans():
    return db.session.scalars(db.select(Loan)).all()


def get_all_loans_json():
    return [_loan_to_dict(loan) for loan in get_all_loans()]


# ---------------------------------------------------------------------------
# Filtered queries
# ---------------------------------------------------------------------------


def get_active_loans():
    """Return all loans that have not yet been returned."""
    return db.session.scalars(db.select(Loan).where(Loan.returnDate.is_(None))).all()


def get_active_loans_json():
    return [_loan_to_dict(loan) for loan in get_active_loans()]


def get_returned_loans():
    """Return all loans that have been returned."""
    return db.session.scalars(db.select(Loan).where(Loan.returnDate.isnot(None))).all()


def get_returned_loans_json():
    return [_loan_to_dict(loan) for loan in get_returned_loans()]


def get_loans_by_patron(patronID):
    """Return all loans for a given patron."""
    return db.session.scalars(db.select(Loan).where(Loan.patronID == patronID)).all()


def get_loans_by_patron_json(patronID):
    return [_loan_to_dict(loan) for loan in get_loans_by_patron(patronID)]


def get_loans_by_staff(staffUserID):
    """Return all loans processed by a given staff user."""
    return db.session.scalars(
        db.select(Loan).where(Loan.processedByStaffUserID == staffUserID)
    ).all()


def get_loans_by_staff_json(staffUserID):
    return [_loan_to_dict(loan) for loan in get_loans_by_staff(staffUserID)]


# ---------------------------------------------------------------------------
# Return
# ---------------------------------------------------------------------------


def return_loan(loanID, returnDate=None, damage_notes=None, file_conditions=None):
    """Mark a loan as returned and set all its files back to 'Available'.

    Args:
        loanID: The ID of the loan to return.
        returnDate: Optional datetime; defaults to now.

    Returns:
        The updated Loan instance, or None on failure.
    """
    loan = get_loan(loanID)
    if not loan:
        print(f"Loan with ID {loanID} not found.")
        return None
 
    if loan.returnDate is not None:
        print(f"Loan {loanID} has already been returned on {loan.returnDate}.")
        return loan  # idempotent
 
    try:
        loan.returnDate = returnDate or datetime.utcnow()
        if damage_notes:
            loan.damageNotes = damage_notes
 
        file_conditions = file_conditions or {}
        for file in loan.files:
            note = file_conditions.get(file.fileID, '').strip()
            if note:
                file.conditionNotes = note
            file.status = "Available"
            file.loanID = None
 
        db.session.commit()
        return loan
    except Exception as e:
        db.session.rollback()
        print(f"Error returning loan {loanID}: {e}")
        return None

# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def update_loan(
    loanID, patronID=None, processedByStaffUserID=None, loanDate=None, returnDate=None
):
    """Update mutable fields on an existing Loan.

    Only the keyword arguments that are explicitly provided (i.e. not None)
    are changed.
    """
    loan = get_loan(loanID)
    if not loan:
        print(f"Loan with ID {loanID} not found.")
        return None

    try:
        if patronID is not None:
            patron = db.session.get(Patron, patronID)
            if not patron:
                print(f"Patron with ID {patronID} not found.")
                return None
            loan.patronID = patronID

        if processedByStaffUserID is not None:
            staff = db.session.get(StaffUser, processedByStaffUserID)
            if not staff:
                print(f"StaffUser with ID {processedByStaffUserID} not found.")
                return None
            loan.processedByStaffUserID = processedByStaffUserID

        if loanDate is not None:
            if isinstance(loanDate, str):
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
                    try:
                        loanDate = datetime.strptime(loanDate, fmt)
                        break
                    except ValueError:
                        continue
            loan.loanDate = loanDate
        if returnDate is not None:
            if isinstance(returnDate, str):
                for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
                    try:
                        returnDate = datetime.strptime(returnDate, fmt)
                        break
                    except ValueError:
                        continue
            loan.returnDate = returnDate

        db.session.commit()
        return loan
    except Exception as e:
        db.session.rollback()
        print(f"Error updating loan {loanID}: {e}")
        return None


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def delete_loan(loanID):
    """Delete a loan record.  Associated files are detached (loanID set to
    None) before deletion so no FK constraint is violated."""
    loan = get_loan(loanID)
    if not loan:
        print(f"Loan with ID {loanID} not found.")
        return False
    try:
        for file in loan.files:
            file.loanID = None
            file.status = "Available"
        db.session.delete(loan)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting loan {loanID}: {e}")
        return False


# ---------------------------------------------------------------------------
# Relationship helpers
# ---------------------------------------------------------------------------


def get_loan_files(loanID):
    """Return all File records currently attached to a loan."""
    loan = get_loan(loanID)
    if not loan:
        return None
    return loan.files


def get_loan_files_json(loanID):
    files = get_loan_files(loanID)
    if files is None:
        return None
    return [
        {
            "fileID": f.fileID,
            "fileType": f.fileType,
            "description": f.description,
            "previousDesignation": f.previousDesignation,
            "status": f.status,
            "conditionNotes": f.conditionNotes or None,
            "boxID": f.boxID,
            "locationID": f.locationID,
            "dateCreated": str(f.dateCreated),
        }
        for f in files
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _loan_to_dict(loan):
    
    processed_by = None
    if loan.processedByStaffUserID:
        staff = db.session.get(StaffUser, loan.processedByStaffUserID)
        if staff and staff.user:
            processed_by = staff.user.username
            
    return {
        "loanID": loan.loanID,
        "loanDate": str(loan.loanDate),
        "returnDate": str(loan.returnDate) if loan.returnDate else None,
        "damageNotes": loan.damageNotes or None,
        "processedByStaffUserID": loan.processedByStaffUserID,
        "patronID": loan.patronID,
        "fileCount": len(loan.files),
    }
