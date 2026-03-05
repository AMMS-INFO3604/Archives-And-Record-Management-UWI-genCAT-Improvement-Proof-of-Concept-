from App.database import db
from App.models import Location


def create_location(geoLocation):
    location = Location(geoLocation=geoLocation)
    try:
        db.session.add(location)
        db.session.commit()
        return location
    except Exception as e:
        db.session.rollback()
        print(f"Error creating location: {e}")
        return None


def get_location(locationID):
    return db.session.get(Location, locationID)


def get_location_by_name(geoLocation):
    return db.session.execute(
        db.select(Location).filter_by(geoLocation=geoLocation)
    ).scalar_one_or_none()


def get_all_locations():
    return db.session.scalars(db.select(Location)).all()


def update_location(locationID, geoLocation):
    location = get_location(locationID)
    if not location:
        print(f"Location with ID {locationID} not found.")
        return None
    try:
        location.geoLocation = geoLocation
        db.session.commit()
        return location
    except Exception as e:
        db.session.rollback()
        print(f"Error updating location {locationID}: {e}")
        return None


def delete_location(locationID):
    location = get_location(locationID)
    if not location:
        print(f"Location with ID {locationID} not found.")
        return False
    try:
        db.session.delete(location)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting location {locationID}: {e}")
        return False
