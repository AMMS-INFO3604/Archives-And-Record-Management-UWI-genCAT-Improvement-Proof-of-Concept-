from datetime import datetime, timedelta

from App.database import db
from App.models import (
    Box,
    File,
    Loan,
    Location,
    Patron,
    StaffRecord,
    StaffUser,
    Student,
    User,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _add(obj):
    """Add an object to the session and flush so its PK is available."""
    db.session.add(obj)
    db.session.flush()
    return obj


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def initialize():
    """Drop all tables, recreate them, then populate with seed data."""
    db.drop_all()
    db.create_all()
    _seed()
    print("Database initialised and seeded successfully.")


def _seed():
    # ------------------------------------------------------------------
    # 1. Locations  (only 2, matching the web app location selection)
    # ------------------------------------------------------------------
    loc1 = _add(Location(geoLocation="Lloyd Brathwaite Building"))
    loc2 = _add(Location(geoLocation="South Campus"))

    # ------------------------------------------------------------------
    # 2. Boxes
    # ------------------------------------------------------------------
    box1 = _add(
        Box(
            bayNo=1,
            rowNo=1,
            columnNo=1,
            barcode="BOX-LB-001",
            locationID=loc1.locationID,
        )
    )
    box2 = _add(
        Box(
            bayNo=1,
            rowNo=1,
            columnNo=2,
            barcode="BOX-LB-002",
            locationID=loc1.locationID,
        )
    )
    box3 = _add(
        Box(
            bayNo=1,
            rowNo=2,
            columnNo=1,
            barcode="BOX-LB-003",
            locationID=loc1.locationID,
        )
    )
    box4 = _add(
        Box(
            bayNo=2,
            rowNo=1,
            columnNo=1,
            barcode="BOX-SC-001",
            locationID=loc2.locationID,
        )
    )
    box5 = _add(
        Box(
            bayNo=2,
            rowNo=1,
            columnNo=2,
            barcode="BOX-SC-002",
            locationID=loc2.locationID,
        )
    )
    box6 = _add(
        Box(
            bayNo=1,
            rowNo=3,
            columnNo=1,
            barcode="BOX-SC-003",
            locationID=loc2.locationID,
        )
    )
    box7 = _add(
        Box(
            bayNo=1,
            rowNo=1,
            columnNo=1,
            barcode="BOX-LB-REG-001",
            locationID=loc1.locationID,
        )
    )

    # ------------------------------------------------------------------
    # 3. Users  (staff first, then patrons)
    # ------------------------------------------------------------------
    u_admin = _add(User(username="admin", password="adminpass"))
    u_alice = _add(User(username="alice", password="alicepass"))
    u_bob = _add(User(username="bob", password="bobpass"))

    u_carol = _add(User(username="carol", password="carolpass"))
    u_dave = _add(User(username="dave", password="davepass"))
    u_eve = _add(User(username="eve", password="evepass"))
    u_frank = _add(User(username="frank", password="frankpass"))
    u_grace = _add(User(username="grace", password="gracepass"))

    # ------------------------------------------------------------------
    # 4. StaffUser profiles
    # ------------------------------------------------------------------
    su_admin = _add(StaffUser(userID=u_admin.userID))
    su_alice = _add(StaffUser(userID=u_alice.userID))
    su_bob = _add(StaffUser(userID=u_bob.userID))

    # ------------------------------------------------------------------
    # 5. Patron profiles
    # ------------------------------------------------------------------
    p_carol = _add(Patron(userID=u_carol.userID))
    p_dave = _add(Patron(userID=u_dave.userID))
    p_eve = _add(Patron(userID=u_eve.userID))
    p_frank = _add(Patron(userID=u_frank.userID))
    p_grace = _add(Patron(userID=u_grace.userID))

    # ------------------------------------------------------------------
    # 6. Files  (student files)
    # ------------------------------------------------------------------
    now = datetime.utcnow()

    sf1 = _add(
        File(
            boxID=box1.boxID,
            fileType="Student",
            description="Undergraduate transcript – BSc Computer Science",
            previousDesignation="T/CS/2018/001",
            createdByStaffUserID=su_admin.staffUserID,
            dateCreated=now - timedelta(days=730),
            status="Available",
        )
    )
    sf2 = _add(
        File(
            boxID=box1.boxID,
            fileType="Student",
            description="Undergraduate transcript – BSc Information Technology",
            previousDesignation="T/IT/2018/002",
            createdByStaffUserID=su_alice.staffUserID,
            dateCreated=now - timedelta(days=700),
            status="Available",
        )
    )
    sf3 = _add(
        File(
            boxID=box2.boxID,
            fileType="Student",
            description="Postgraduate transcript – MSc Data Science",
            previousDesignation="T/DS/2020/001",
            createdByStaffUserID=su_alice.staffUserID,
            dateCreated=now - timedelta(days=500),
            status="Available",
        )
    )
    sf4 = _add(
        File(
            boxID=box2.boxID,
            fileType="Student",
            description="Undergraduate transcript – BA Economics",
            previousDesignation="T/EC/2019/003",
            createdByStaffUserID=su_bob.staffUserID,
            dateCreated=now - timedelta(days=450),
            status="Available",
        )
    )
    sf5 = _add(
        File(
            boxID=box3.boxID,
            fileType="Student",
            description="Diploma in Management Studies",
            previousDesignation="D/MS/2021/001",
            createdByStaffUserID=su_admin.staffUserID,
            dateCreated=now - timedelta(days=300),
            status="Available",
        )
    )
    sf6 = _add(
        File(
            boxID=box3.boxID,
            fileType="Student",
            description="Certificate in Public Administration",
            previousDesignation="C/PA/2022/001",
            createdByStaffUserID=su_alice.staffUserID,
            dateCreated=now - timedelta(days=200),
            status="Available",
        )
    )

    # Staff personnel files
    pf1 = _add(
        File(
            boxID=box7.boxID,
            fileType="Staff",
            description="Personnel file – Senior Lecturer",
            previousDesignation="PF/SL/2015/001",
            createdByStaffUserID=su_admin.staffUserID,
            dateCreated=now - timedelta(days=2000),
            status="Available",
        )
    )
    pf2 = _add(
        File(
            boxID=box7.boxID,
            fileType="Staff",
            description="Personnel file – Administrative Officer",
            previousDesignation="PF/AO/2017/002",
            createdByStaffUserID=su_admin.staffUserID,
            dateCreated=now - timedelta(days=1800),
            status="Available",
        )
    )
    pf3 = _add(
        File(
            boxID=box6.boxID,
            fileType="Staff",
            description="Personnel file – Research Fellow",
            previousDesignation="PF/RF/2019/003",
            createdByStaffUserID=su_bob.staffUserID,
            dateCreated=now - timedelta(days=1200),
            status="Available",
        )
    )

    loan_file1 = _add(
        File(
            boxID=box4.boxID,
            fileType="Student",
            description="Undergraduate transcript – BSc Mathematics",
            previousDesignation="T/MA/2020/004",
            createdByStaffUserID=su_alice.staffUserID,
            dateCreated=now - timedelta(days=400),
            status="Available",
        )
    )
    loan_file2 = _add(
        File(
            boxID=box5.boxID,
            fileType="Student",
            description="Postgraduate transcript – MA History",
            previousDesignation="T/HI/2021/005",
            createdByStaffUserID=su_bob.staffUserID,
            dateCreated=now - timedelta(days=380),
            status="Available",
        )
    )

    # ------------------------------------------------------------------
    # 7. Student records
    # ------------------------------------------------------------------
    _add(Student(fileID=sf1.fileID, certificateDiploma="BSc Computer Science", code="810002345"))
    _add(Student(fileID=sf2.fileID, certificateDiploma="BSc Information Technology", code="810003456"))
    _add(Student(fileID=sf3.fileID, certificateDiploma="MSc Data Science", code="816001234"))
    _add(Student(fileID=sf4.fileID, certificateDiploma="BA Economics", code="810009876"))
    _add(Student(fileID=sf5.fileID, certificateDiploma="Diploma in Management Studies", code="DMS2021-007"))
    _add(Student(fileID=sf6.fileID, certificateDiploma="Certificate in Public Administration", code="CPA2022-003"))
    _add(Student(fileID=loan_file1.fileID, certificateDiploma="BSc Mathematics", code="810007654"))
    _add(Student(fileID=loan_file2.fileID, certificateDiploma="MA History", code="816004321"))

    # ------------------------------------------------------------------
    # 8. Staff records
    # ------------------------------------------------------------------
    _add(StaffRecord(
        fileID=pf1.fileID, fileNumber="SL-2015-001",
        fileTitle="Academic Appointment – Senior Lecturer",
        post="Senior Lecturer", organisationUnit="Faculty of Science & Technology",
        notes="Tenure track appointment, started January 2015.",
    ))
    _add(StaffRecord(
        fileID=pf2.fileID, fileNumber="AO-2017-002",
        fileTitle="Administrative Appointment – Registry",
        post="Administrative Officer II", organisationUnit="Registry",
        notes="Transferred from Faculty of Humanities in 2019.",
    ))
    _add(StaffRecord(
        fileID=pf3.fileID, fileNumber="RF-2019-003",
        fileTitle="Research Appointment – Institute for Critical Thinking",
        post="Research Fellow", organisationUnit="Institute for Critical Thinking & Writing",
        notes="Fixed-term contract renewed twice.",
    ))

    # ------------------------------------------------------------------
    # 9. Loans
    # ------------------------------------------------------------------
    now = datetime.utcnow()

    rl1 = _add(Loan(
        patronID=p_carol.patronID,
        processedByStaffUserID=su_alice.staffUserID,
        loanDate=now - timedelta(days=60),
        returnDate=now - timedelta(days=45),
    ))

    rl2 = _add(Loan(
        patronID=p_dave.patronID,
        processedByStaffUserID=su_bob.staffUserID,
        loanDate=now - timedelta(days=90),
        returnDate=now - timedelta(days=80),
    ))

    rl3 = _add(Loan(
        patronID=p_eve.patronID,
        processedByStaffUserID=su_admin.staffUserID,
        loanDate=now - timedelta(days=120),
        returnDate=now - timedelta(days=100),
    ))

    al1 = _add(Loan(
        patronID=p_frank.patronID,
        processedByStaffUserID=su_alice.staffUserID,
        loanDate=now - timedelta(days=10),
        returnDate=None,
    ))
    loan_file1.loanID = al1.loanID
    loan_file1.status = "On Loan"

    al2 = _add(Loan(
        patronID=p_grace.patronID,
        processedByStaffUserID=su_bob.staffUserID,
        loanDate=now - timedelta(days=5),
        returnDate=None,
    ))
    loan_file2.loanID = al2.loanID
    loan_file2.status = "On Loan"

    # ------------------------------------------------------------------
    # 10. Commit everything
    # ------------------------------------------------------------------
    db.session.commit()

    print(f"  Locations  : {Location.query.count()}")
    print(f"  Boxes      : {Box.query.count()}")
    print(f"  Users      : {User.query.count()}")
    print(f"  StaffUsers : {StaffUser.query.count()}")
    print(f"  Patrons    : {Patron.query.count()}")
    print(f"  Files      : {File.query.count()}")
    print(f"  Students   : {Student.query.count()}")
    print(f"  StaffRecs  : {StaffRecord.query.count()}")
    print(f"  Loans      : {Loan.query.count()}")
    print(f"  Active loans: {Loan.query.filter_by(returnDate=None).count()}")