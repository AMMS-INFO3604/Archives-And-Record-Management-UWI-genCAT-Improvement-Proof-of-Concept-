
from App.database import db
from App.models import Box, File, Location, User
from datetime import datetime, date as _date


def _parse_date(value):
    """Coerce a date string, date, or datetime into a datetime (or None)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, _date):                          # date but not datetime
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str) and value.strip():
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
    return None


def addFile(
    boxID,
    fileType,
    locationID=None,
    loanID=None,
    description=None,
    previousDesignation=None,
    createdByStaffUserID=None,
    dateCreated=None,
    status=None,
    barcode=None,
):
    newfile = File(
        boxID=boxID,
        locationID=locationID,
        loanID=loanID,
        fileType=fileType,
        description=description,
        previousDesignation=previousDesignation,
        createdByStaffUserID=createdByStaffUserID,
        dateCreated=_parse_date(dateCreated),
        status=status or "Available",
        barcode=barcode,
    )
    try:
        db.session.add(newfile)
        db.session.commit()
        return newfile
    except Exception as e:
        db.session.rollback()
        print(f"addFile error: {e}")
        return None


def updateFile(
    fileID,
    boxID=None,
    locationID=None,
    loanID=None,
    fileType=None,
    description=None,
    previousDesignation=None,
    createdByStaffUserID=None,
    dateCreated=None,
    status=None,
    barcode=None,
):
    file = db.session.get(File, fileID)
    if not file:
        return None

    if boxID is not None:
        file.boxID = boxID
    if locationID is not None:
        file.locationID = locationID
    if loanID is not None:
        file.loanID = loanID
    if fileType is not None:
        file.fileType = fileType
    if description is not None:
        file.description = description
    if previousDesignation is not None:
        file.previousDesignation = previousDesignation
    if createdByStaffUserID is not None:
        file.createdByStaffUserID = createdByStaffUserID
    if dateCreated is not None:
        file.dateCreated = _parse_date(dateCreated)
    if status is not None:
        file.status = status
    if barcode is not None:
        file.barcode = barcode

    try:
        db.session.commit()
        return file
    except Exception as e:
        db.session.rollback()
        print(f"updateFile error: {e}")
        return None


def searchFile(
    fileID=None, fileType=None, locationID=None, loanID=None,
    status=None, keyword=None, date_from=None, date_to=None
):
    stmt = db.select(File)

    if fileID is not None:
        stmt = stmt.where(File.fileID == fileID)
    if fileType is not None:
        stmt = stmt.where(File.fileType == fileType)
    if locationID is not None:
        stmt = stmt.where(File.locationID == locationID)
    if loanID is not None:
        stmt = stmt.where(File.loanID == loanID)
    if status is not None:
        stmt = stmt.where(File.status == status)
    if keyword is not None:
        pattern = f"%{keyword}%"
        stmt = stmt.where(
            db.or_(
                File.description.ilike(pattern),
                File.previousDesignation.ilike(pattern),
            )
        )
    if date_from:
        try:
            df = datetime.strptime(date_from, "%Y-%m-%d").date()
            stmt = stmt.where(File.dateCreated >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").date()
            stmt = stmt.where(File.dateCreated <= dt)
        except Exception:
            pass

    return db.session.scalars(stmt).all()


def deleteFile(fileID):
    file = db.session.get(File, fileID)
    if not file:
        print(f"File with ID {fileID} not found")
        return False
    try:
        db.session.delete(file)
        db.session.commit()
        print(f"File with ID {fileID} deleted successfully")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"deleteFile error: {e}")
        return False


def viewFile(fileID):
    file = db.session.get(File, fileID)
    if not file:
        print(f"File with ID {fileID} not found")
        return None
    return file


def getAllFiles():
    return db.session.scalars(db.select(File)).all()


def changeFileStatus(fileID, newStatus):
    file = db.session.get(File, fileID)
    if not file:
        print(f"File with ID {fileID} not found")
        return None
    file.status = newStatus
    try:
        db.session.commit()
        return file
    except Exception as e:
        db.session.rollback()
        print(f"changeFileStatus error: {e}")
        return None