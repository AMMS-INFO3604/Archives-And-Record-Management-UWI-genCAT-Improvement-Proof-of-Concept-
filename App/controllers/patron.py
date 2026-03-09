from App.database import db
from App.models import Patron


def create_patron(userID):
    patron = Patron(userID=userID)
    try:
        db.session.add(patron)
        db.session.commit()
        return patron
    except Exception as e:
        db.session.rollback()
        print(f"Error creating patron: {e}")
        return None


def get_patron(patronID):
    return db.session.get(Patron, patronID)


def get_patron_by_user(userID):
    return db.session.execute(
        db.select(Patron).filter_by(userID=userID)
    ).scalar_one_or_none()


def get_all_patrons():
    return db.session.scalars(db.select(Patron)).all()


def delete_patron(patronID):
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
