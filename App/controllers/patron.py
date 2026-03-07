from App.database import db
from App.models import Patron, User

# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def create_patron(userID):
    """Create a Patron profile linked to an existing User."""
    user = db.session.get(User, userID)
    if not user:
        print(f"User with ID {userID} not found.")
        return None

    existing = get_patron_by_user(userID)
    if existing:
        print(f"A Patron profile already exists for user {userID}.")
        return None

    patron = Patron(userID=userID)
    try:
        db.session.add(patron)
        db.session.commit()
        return patron
    except Exception as e:
        db.session.rollback()
        print(f"Error creating patron: {e}")
        return None


# ---------------------------------------------------------------------------
# Read – single record
# ---------------------------------------------------------------------------


def get_patron(patronID):
    """Return a Patron by its primary key."""
    return db.session.get(Patron, patronID)


def get_patron_by_user(userID):
    """Return the Patron profile associated with a given userID."""
    return db.session.execute(
        db.select(Patron).filter_by(userID=userID)
    ).scalar_one_or_none()


def get_patron_json(patronID):
    patron = get_patron(patronID)
    if not patron:
        return None
    return {
        "patronID": patron.patronID,
        "userID": patron.userID,
    }


# ---------------------------------------------------------------------------
# Read – all records
# ---------------------------------------------------------------------------


def get_all_patrons():
    return db.session.scalars(db.select(Patron)).all()


def get_all_patrons_json():
    return [{"patronID": p.patronID, "userID": p.userID} for p in get_all_patrons()]


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def update_patron(patronID, userID):
    """Reassign the Patron profile to a different User account."""
    patron = get_patron(patronID)
    if not patron:
        print(f"Patron with ID {patronID} not found.")
        return None

    user = db.session.get(User, userID)
    if not user:
        print(f"User with ID {userID} not found.")
        return None

    try:
        patron.userID = userID
        db.session.commit()
        return patron
    except Exception as e:
        db.session.rollback()
        print(f"Error updating patron {patronID}: {e}")
        return None


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def delete_patron(patronID):
    """Delete a Patron profile by its primary key."""
    patron = get_patron(patronID)
    if not patron:
        print(f"Patron with ID {patronID} not found.")
        return False
    try:
        db.session.delete(patron)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting patron {patronID}: {e}")
        return False


# ---------------------------------------------------------------------------
# Relationship helpers
# ---------------------------------------------------------------------------


def get_patron_loans(patronID):
    """Return all Loan records for a given patron."""
    patron = get_patron(patronID)
    if not patron:
        return None
    return patron.loans


def get_patron_loans_json(patronID):
    loans = get_patron_loans(patronID)
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
