from sqlalchemy import func

from App.database import db
from App.models import Box, Location

# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Read – single record
# ---------------------------------------------------------------------------


def get_location(locationID):
    return db.session.get(Location, locationID)


def get_location_by_name(geoLocation):
    return db.session.execute(
        db.select(Location).filter_by(geoLocation=geoLocation)
    ).scalar_one_or_none()


def _box_count(locationID):
    """Return the number of boxes stored at a given location."""
    return db.session.execute(
        db.select(func.count()).select_from(Box).where(Box.locationID == locationID)
    ).scalar()


def get_location_json(locationID):
    location = get_location(locationID)
    if not location:
        return None
    data = location.get_json()
    data["boxCount"] = _box_count(locationID)
    return data


# ---------------------------------------------------------------------------
# Read – all records
# ---------------------------------------------------------------------------


def get_all_locations():
    return db.session.scalars(db.select(Location)).all()


def get_all_locations_json():
    locations = get_all_locations()
    result = []
    for loc in locations:
        data = loc.get_json()
        data["boxCount"] = _box_count(loc.locationID)
        result.append(data)
    return result


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_locations(query):
    """Return all locations whose geoLocation contains *query* (case-insensitive)."""
    pattern = f"%{query}%"
    return db.session.scalars(
        db.select(Location).where(Location.geoLocation.ilike(pattern))
    ).all()


def search_locations_json(query):
    result = []
    for loc in search_locations(query):
        data = loc.get_json()
        data["boxCount"] = _box_count(loc.locationID)
        result.append(data)
    return result


# ---------------------------------------------------------------------------
# Relationship queries
# ---------------------------------------------------------------------------


def get_boxes_at_location(locationID):
    """Return all Box records stored at this location."""
    location = get_location(locationID)
    if not location:
        return None
    return location.boxes


def get_boxes_at_location_json(locationID):
    boxes = get_boxes_at_location(locationID)
    if boxes is None:
        return None
    return [
        {
            "boxID": box.boxID,
            "bayNo": box.bayNo,
            "rowNo": box.rowNo,
            "columnNo": box.columnNo,
            "barcode": box.barcode,
            "locationID": box.locationID,
        }
        for box in boxes
    ]


def get_files_at_location(locationID):
    """Return all File records whose locationID is set to this location
    (files that have been directly assigned to a location, e.g. while on loan
    or awaiting re-shelving)."""
    from App.models import File

    return db.session.scalars(
        db.select(File).where(File.locationID == locationID)
    ).all()


def get_files_at_location_json(locationID):
    files = get_files_at_location(locationID)
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


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


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
