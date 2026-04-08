from App.database import db
from App.models import Box, Location


def addBox(bayNo=None, rowNo=None, columnNo=None, barcode=None, locationID=None):
    newbox = Box(
        bayNo=bayNo,
        rowNo=rowNo,
        columnNo=columnNo,
        barcode=barcode,
        locationID=locationID,
    )

    try:
        db.session.add(newbox)
        db.session.commit()
        return newbox
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while adding box: {e}")
        return None


def updateBox(
    boxID, bayNo=None, rowNo=None, columnNo=None, barcode=None, locationID=None,
    colorStatus=None
):
    box = db.session.get(Box, boxID)

    if not box:
        print(f"Box with ID {boxID} was not found.")
        return None

    if bayNo is not None:
        box.bayNo = bayNo
    if rowNo is not None:
        box.rowNo = rowNo
    if columnNo is not None:
        box.columnNo = columnNo
    if barcode is not None:
        box.barcode = barcode
    if locationID is not None:
        box.locationID = locationID
    if colorStatus is not None:
        box.colorStatus = colorStatus

    try:
        db.session.commit()
        return box
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while updating box with ID {boxID}: {e}")
        return None


def changeBoxStatus(boxID, colorStatus):
    """Update the colour/status label stored directly on the box."""
    box = db.session.get(Box, boxID)
    if not box:
        print(f"Box with ID {boxID} was not found.")
        return None
    box.colorStatus = colorStatus
    try:
        db.session.commit()
        return box
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while changing status for box {boxID}: {e}")
        return None


def moveBoxLocation(boxID, newLocationID):
    box = db.session.get(Box, boxID)

    if not box:
        print(f"Box with ID {boxID} was not found.")
        return None

    location = db.session.get(Location, newLocationID)
    if not location:
        print(f"Location with ID {newLocationID} was not found.")
        return None

    box.locationID = newLocationID

    try:
        db.session.commit()
        print(f"Box with ID {boxID} was moved to location with ID {newLocationID}")
        return box
    except Exception as e:
        db.session.rollback()
        print(
            f"Error occurred while moving box with ID {boxID} "
            f"to location with ID {newLocationID}: {e}"
        )
        return None


def deleteBox(boxID):
    box = db.session.get(Box, boxID)

    if not box:
        print(f"Box with ID {boxID} was not found.")
        return False

    try:
        db.session.delete(box)
        db.session.commit()
        print(f"Box with ID {boxID} was deleted successfully.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while deleting box with ID {boxID}: {e}")
        return False


def getBoxByID(boxID):
    box = db.session.get(Box, boxID)

    if not box:
        print(f"Box with ID {boxID} was not found.")
        return None

    return box


def getAllBoxes():
    return db.session.scalars(db.select(Box)).all()


def getBoxJSON(box):
    """Return a plain dict representation of a Box instance."""
    return {
        "boxID": box.boxID,
        "bayNo": box.bayNo,
        "rowNo": box.rowNo,
        "columnNo": box.columnNo,
        "barcode": box.barcode,
        "locationID": box.locationID,
        "colorStatus": box.colorStatus,
        "color_status": box.color_status,
        "fileCount": len(box.files),
    }


def getAllBoxesJSON():
    return [getBoxJSON(b) for b in getAllBoxes()]


def searchBoxesByLocation(locationID):
    boxes = db.session.scalars(db.select(Box).where(Box.locationID == locationID)).all()

    if not boxes:
        print(f"No boxes found for location with ID {locationID}.")
        return []

    return boxes


def searchBoxesByLocationJSON(locationID):
    return [getBoxJSON(b) for b in searchBoxesByLocation(locationID)]