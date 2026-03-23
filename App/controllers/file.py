# will edit for staffUser usage for certain controllers as well as for patron(Hence only staff can add,delete,update while patron could only search and view files)
from App.database import db
from App.models import Box, File, Location, User
from datetime import datetime

def addFile(
    boxID,
    fileType,
    locationID=None,
    loanID=None,
    description=None,
    previousDesignation=None,
    createdByStaffUserID=None,
    dateCreated=None,
):  # Add the file to the database fileID is auto generated
    newfile = File(
        boxID=boxID,
        locationID=locationID,
        loanID=loanID,
        fileType=fileType,
        description=description,
        previousDesignation=previousDesignation,
        createdByStaffUserID=createdByStaffUserID,
        dateCreated=dateCreated,
        status="Available",
    )
    try:
        db.session.add(newfile)
        db.session.commit()
        return newfile  # Return the newly created file object
    except Exception as e:
        db.session.rollback()
        return None  # Handle the errors As needed


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
):  # Update file info due to fileID, only the provided fields will be updated.
    file = db.session.get(File, fileID)

    if not file:
        return None  # File is not found

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
        file.dateCreated = dateCreated
    if status is not None:
        file.status = status

    try:
        db.session.commit()
        return file
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while updating file with ID {fileID}: {e}")
        return None  # Handle the error as needed


def searchFile(
    fileID=None, fileType=None, locationID=None, loanID=None, status=None, keyword=None, date_from=None,date_to=None
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
         except:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d").date()
            stmt = stmt.where(File.dateCreated <= dt)
        except:
            pass

    return db.session.scalars(stmt).all()


def deleteFile(fileID):  # Delete the file with the fileID from the database.
    file = db.session.get(File, fileID)

    if not file:
        print(f"File with ID {fileID} not found")
        return False  # File is not found

    try:
        db.session.delete(file)
        db.session.commit()
        print(f"File with ID {fileID} deleted successfully")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while deleting file with ID {fileID}")
        return False  # Handle the error as needed


def viewFile(fileID):
    file = db.session.get(File, fileID)

    if not file:
        print(f"File with ID {fileID} not found")
        return None  # File is not found

    return file  # Return the file with the fileID


def getAllFiles():
    return db.session.scalars(db.select(File)).all()


def changeFileStatus(fileID, newStatus):
    file = db.session.get(File, fileID)

    if not file:
        print(f"File with ID {fileID} not found")
        return None  # File is not found

    file.status = newStatus

    try:
        db.session.commit()
        print(f"File with ID {fileID} status updated to {newStatus}")
        return file
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while updating status of file with ID {fileID}: {e}")
        return None  # Handle the error as needed
