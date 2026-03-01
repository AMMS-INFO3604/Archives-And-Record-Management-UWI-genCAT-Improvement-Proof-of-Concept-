from app import db
from models import User, Patron, StaffUser, Location, Box, File, Loan
from datetime import date

def seed():
    with app.app_context():
        # Defining locations 
        lloyd_brathwaithe = Location(name='Records Center, Lloyd Brathwaithe Student Administration Building')
        south_campus = Location(name='Debe')
        db.session.add_all([lloyd_brathwaithe, south_campus])

        # Defining sample boxes
        box1 = Box(bay = 1, row = 2, column = 3, location=lloyd_brathwaithe)
        box2 = Box(bay = 2, row = 1, column = 4, location=south_campus)
        db.session.add_all([box1, box2])

        # Defining sample users
        staff_user = User(email="staff@archives.com", password="password123", userType=True)
        patron_user = User(email="patron@archives.com", password="password123", userType=False)
        db.session.add_all([staff_user, patron_user])

        # Defining sample files
        file1 = File(fileTitle="Student Record - John Doe", type="Student", box=box1)
        file2 = File(fileTitle="Staff Record - Jane Smith", type="Staff", box=box2)
        db.session.add_all([file1, file2])

        # Sample historical loans
        past_loan1 = Loan(
            dateCheckedOut=date(2025, 10, 1),
            dateDue=date(2025, 10, 15),
            dateCheckedIn=date(2025, 10, 13),  
            patronID=patron.patronID,
            fileID=file1.id
        )
        # ^Loan already returned

        past_loan2 = Loan(
            dateCheckedOut=date(2025, 11, 5),
            dateDue=date(2025, 11, 20),
            dateCheckedIn=None,  # Still on loan
            patronID=patron.patronID,
            fileID=file2.id
        )
        # ^Still-active loan

        db.session.add_all([past_loan1, past_loan2])
        db.session.commit()
        print("Users, files and loans seeded successfully!")

if __name__ == "__main__":
    seed()