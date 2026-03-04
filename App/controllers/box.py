from App.models import Box, User, Location, File, box
from App.database import db

def addBox(bayNo=None, rowNo=None, columnNo=None, barcode=None,locationID=None):
    newbox = Box(
        bayNo=bayNo,
        rowNo=rowNo,
        columnNo=columnNo,
        barcode=barcode,
        locationID=locationID
           
    )
    
    try:
        db.session.add(newbox)
        db.session.commit()
        return newbox
    except Exception as e:
        db.session.rollback()
        return None # Handle the error as needed 
        
def updateBox(boxID, bayNo=None, rowNo=None, columnNo=None, barcode=None, locationID=None):
    box = Box.query.get(boxID)
    
    if not box:
        return None # Box is not found
    
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
        
    try:
        db.session.commit()
        return box
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while updating box with ID {boxID}: {e}")
        return None # Handle the error as needed

def moveBoxLocation(boxID, newLocationID):
    box = Box.query.get(boxID)
    
    if not box: 
        return None # Bos was not found
    
    box.locationID = newLocationID
    
    try:
        db.session.commit()
        print(f"Box with ID {boxID} was moved to location with ID {newLocationID}")
        return box
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while moving box with ID {boxID} to location with ID {newLocationID}: {e}")
        return None # Handle the error as needed

def deleteBox(boxID):
    box = Box.query.get(boxID)
    
    if not box:
        print(f"Box with ID {boxID} was not found.")
        return False # Box was not found
    
    try:
        db.session.delete(box)
        db.session.commit()
        print(f"Box with ID {boxID} was deleted successfully.")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred while deleting box with ID {boxID}: {e}")
        return False # Handle the error as needed
    
def getBoxByID(boxID):
    box = Box.query.get(boxID)
    
    if not box:
     print(f"Box with ID {boxID} was not found.")
     return None # Box was not found
  
    return box 

    

def getAllBoxes():
    return Box.query.all()

def searchBoxesByLocation(locationID):
    box = Box.query.filter(Box.locationID == locationID).all()
    
    if not box:
        print(f"No boxes found for location with ID {locationID}.")
        return None # No boxes found for the given location
    return box
