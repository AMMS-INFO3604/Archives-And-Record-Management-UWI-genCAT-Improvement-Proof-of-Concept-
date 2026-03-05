from App.database import db
from App.models import StaffUser


def create_staff_user(userID):
    staff = StaffUser(userID=userID)
    try:
        db.session.add(staff)
        db.session.commit()
        return staff
    except Exception as e:
        db.session.rollback()
        print(f"Error creating staff user: {e}")
        return None


def get_staff_user(staffUserID):
    return db.session.get(StaffUser, staffUserID)


def get_staff_user_by_user(userID):
    return db.session.execute(
        db.select(StaffUser).filter_by(userID=userID)
    ).scalar_one_or_none()


def get_all_staff_users():
    return db.session.scalars(db.select(StaffUser)).all()


def delete_staff_user(staffUserID):
    staff = get_staff_user(staffUserID)
    if not staff:
        print(f"Staff user with ID {staffUserID} not found.")
        return False
    try:
        db.session.delete(staff)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting staff user {staffUserID}: {e}")
        return False
