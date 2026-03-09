from datetime import datetime

from App.database import db
from App.models import Loan


def create_loan(patronID, processedByStaffUserID=None, loanDate=None):
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


def get_loan(loanID):
    return db.session.get(Loan, loanID)


def get_all_loans():
    return db.session.scalars(db.select(Loan)).all()


def get_loans_by_patron(patronID):
    return db.session.scalars(db.select(Loan).filter_by(patronID=patronID)).all()


def get_active_loans():
    """Return all loans that have not yet been returned."""
    return db.session.scalars(db.select(Loan).filter(Loan.returnDate.is_(None))).all()


def return_loan(loanID, returnDate=None):
    loan = get_loan(loanID)
    if not loan:
        print(f"Loan with ID {loanID} not found.")
        return None
    try:
        loan.returnDate = returnDate or datetime.utcnow()
        db.session.commit()
        return loan
    except Exception as e:
        db.session.rollback()
        print(f"Error returning loan {loanID}: {e}")
        return None


def delete_loan(loanID):
    loan = get_loan(loanID)
    if not loan:
        print(f"Loan with ID {loanID} not found.")
        return False
    try:
        db.session.delete(loan)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting loan {loanID}: {e}")
        return False
