from App.database import db
from App.models import StaffUser, User

# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_staff_user(userID):
    """Create a StaffUser profile linked to an existing User."""
    user = db.session.get(User, userID)
    if not user:
        print(f"User with ID {userID} not found.")
        return None

    existing = get_staff_user_by_user(userID)
    if existing:
        print(f"A StaffUser profile already exists for user {userID}.")
        return None

    staff_user = StaffUser(userID=userID)
    try:
        db.session.add(staff_user)
        db.session.commit()
        return staff_user
    except Exception as e:
        db.session.rollback()
        print(f"Error creating staff user: {e}")
        return None


# ---------------------------------------------------------------------------
# Read – single record
# ---------------------------------------------------------------------------


def get_staff_user(staffUserID):
    """Return a StaffUser by its primary key."""
    return db.session.get(StaffUser, staffUserID)


def get_staff_user_by_user(userID):
    """Return the StaffUser profile associated with a given userID."""
    return db.session.execute(
        db.select(StaffUser).filter_by(userID=userID)
    ).scalar_one_or_none()


def get_staff_user_json(staffUserID):
    staff_user = get_staff_user(staffUserID)
    if not staff_user:
        return None
    return {
        "staffUserID": staff_user.staffUserID,
        "userID": staff_user.userID,
    }


# ---------------------------------------------------------------------------
# Read – all records
# ---------------------------------------------------------------------------


def get_all_staff_users():
    return db.session.scalars(db.select(StaffUser)).all()


def get_all_staff_users_json():
    return [
        {"staffUserID": s.staffUserID, "userID": s.userID}
        for s in get_all_staff_users()
    ]


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def update_staff_user(staffUserID, userID):
    """Reassign the StaffUser profile to a different User account."""
    staff_user = get_staff_user(staffUserID)
    if not staff_user:
        print(f"StaffUser with ID {staffUserID} not found.")
        return None

    user = db.session.get(User, userID)
    if not user:
        print(f"User with ID {userID} not found.")
        return None

    try:
        staff_user.userID = userID
        db.session.commit()
        return staff_user
    except Exception as e:
        db.session.rollback()
        print(f"Error updating staff user {staffUserID}: {e}")
        return None


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def delete_staff_user(staffUserID):
    """Delete a StaffUser profile by its primary key."""
    staff_user = get_staff_user(staffUserID)
    if not staff_user:
        print(f"StaffUser with ID {staffUserID} not found.")
        return False
    try:
        db.session.delete(staff_user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting staff user {staffUserID}: {e}")
        return False


# ---------------------------------------------------------------------------
# Relationship helpers
# ---------------------------------------------------------------------------


def get_staff_user_loans(staffUserID):
    """Return all Loan records processed by a given staff user."""
    staff_user = get_staff_user(staffUserID)
    if not staff_user:
        return None
    return staff_user.loans_processed


def get_staff_user_loans_json(staffUserID):
    loans = get_staff_user_loans(staffUserID)
    if loans is None:
        return None
    return [
        {
            "loanID": loan.loanID,
            "loanDate": str(loan.loanDate),
            "returnDate": str(loan.returnDate) if loan.returnDate else None,
            "processedByStaffUserID": loan.processedByStaffUserID,
            "patronID": loan.patronID,
        }
        for loan in loans
    ]


def get_staff_user_files(staffUserID):
    """Return all File records created by a given staff user."""
    staff_user = get_staff_user(staffUserID)
    if not staff_user:
        return None
    return staff_user.files_created


def get_staff_user_files_json(staffUserID):
    files = get_staff_user_files(staffUserID)
    if files is None:
        return None
    return [
        {
            "fileID": f.fileID,
            "fileType": f.fileType,
            "description": f.description,
            "previousDesignation": f.previousDesignation,
            "status": f.status,
            "boxID": f.boxID,
            "locationID": f.locationID,
            "dateCreated": str(f.dateCreated),
        }
        for f in files
    ]
