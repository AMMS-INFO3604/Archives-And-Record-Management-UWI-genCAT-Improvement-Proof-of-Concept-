#will edit for staffUser usage for certain controllers as well as for patron(Hence only staff can add,delete,update while patron could only search and view files)
from App.models import File,Box,User,Location
from App.database import db 

def addFile( boxID, fileType,locationID=None, loanID=None, 
             description=None, previousDesignation=None, 
             createdByStaffUserID=None, dateCreated=None): # Add the file to the database fileID is auto generated
    newfile = File(
        boxID=boxID,
        locationID=locationID,
        loanID=loanID,
        fileType=fileType,
        description=description,
        previousDesignation=previousDesignation,
        createdByStaffUserID=createdByStaffUserID,
        dateCreated=dateCreated,
        status='Available'
    )
    try:
     db.session.add(newfile)
     db.session.commit()
     return newfile # Return the newly created file object
    except Exception as e:
      db.session.rollback()
      return None # Handle the errors As needed

def updateFile(fileID, boxID=None, locationID=None, loanID=None, 
               fileType=None, description=None, previousDesignation=None, 
               createdByStaffUserID=None, dateCreated=None, status=None): # Update file info due to fileID, only the provided fields will be updated.
   file = File.query.get(fileID)
   
   if not file:
       return None # File is not found
      
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
     return None # Handle the error as needed
    
    
def searchFile(fileID=None,fileType=None, locationID=None, loanID=None, status=None): 
        query = File.query          
        
        if fileID is not None:
            query = query.filter_by(fileID=fileID)
        if fileType is not None:
            query = query.filter_by(fileType=fileType)
        if locationID is not None:
            query = query.filter_by(locationID=locationID)
        if loanID is not None:
            query = query.filter_by(loanID=loanID)
        if status is not None:
            query = query.filter_by(status=status)
        
        return query.all()
    
def deleteFile(fileID): # Delete the file with the fileID from the database.
    file = File.query.get(fileID)
    
    if not file:
        print(f"File with ID {fileID} not found")
        return False # File is not found
    
    try:
        db.session.delete(file)
        db.session.commit()
        print(f"File with ID {fileID} deleted successfully")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while deleting file with ID {fileID}")
        return False # Handle the error as needed
 
def viewFile(fileID):
    file = File.query.get(fileID)
    
    if not file:
        print(f"File with ID {fileID} not found")
        return None # File is not found
    
    return file # Return the file with the fileID  

def getAllFiles():
    return File.query.all() # Get a list of all file  in the database

def changeFileStatus(fileID, newStatus):
    file = File.query.get(fileID)
    
    if not file:
        print(f"File with ID {fileID} not found")
        return None # File is not found
    
    file.status = newStatus
    
    try:
        db.session.commit()
        print(f"File with ID {fileID} status updated to {newStatus}")
        return file
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while updating status of file with ID {fileID}: {e}")
        return None # Handle the error as needed 
