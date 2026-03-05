from datetime import datetime

from App.database import db

from .box import addBox
from .file import addFile
from .fileRecord import create_staff_record, create_student_record
from .loan import create_loan, return_loan
from .location import create_location
from .patron import create_patron
from .staffUser import create_staff_user
from .user import create_user


def initialize():
    db.drop_all()
    db.create_all()

    # -------------------------------------------------------------------------
    # Locations
    # -------------------------------------------------------------------------
    loc1 = create_location("Block A - Room 101, Records Storage Wing")
    loc2 = create_location("Block B - Basement Vault")
    loc3 = create_location("Block C - Offsite Archive Facility")

    # -------------------------------------------------------------------------
    # Staff accounts (User + StaffUser profile)
    # -------------------------------------------------------------------------
    u_admin = create_user("admin", "adminpass")
    u_staff1 = create_user("jcampbell", "jcpass")
    u_staff2 = create_user("mthomas", "mtpass")

    staff_admin = create_staff_user(u_admin.userID)
    staff1 = create_staff_user(u_staff1.userID)
    staff2 = create_staff_user(u_staff2.userID)

    # -------------------------------------------------------------------------
    # Patron accounts (User + Patron profile)
    # -------------------------------------------------------------------------
    u_patron1 = create_user("rwilliams", "rwpass")
    u_patron2 = create_user("tjohnson", "tjpass")
    u_patron3 = create_user("asmith", "aspass")
    u_patron4 = create_user("kbrown", "kbpass")

    patron1 = create_patron(u_patron1.userID)
    patron2 = create_patron(u_patron2.userID)
    patron3 = create_patron(u_patron3.userID)
    patron4 = create_patron(u_patron4.userID)

    # -------------------------------------------------------------------------
    # Boxes  (bay / row / column / barcode / location)
    # -------------------------------------------------------------------------
    box1 = addBox(
        bayNo=1, rowNo=1, columnNo=1, barcode="BOX-A-001", locationID=loc1.locationID
    )
    box2 = addBox(
        bayNo=1, rowNo=1, columnNo=2, barcode="BOX-A-002", locationID=loc1.locationID
    )
    box3 = addBox(
        bayNo=1, rowNo=2, columnNo=1, barcode="BOX-A-003", locationID=loc1.locationID
    )
    box4 = addBox(
        bayNo=2, rowNo=1, columnNo=1, barcode="BOX-B-001", locationID=loc2.locationID
    )
    box5 = addBox(
        bayNo=2, rowNo=1, columnNo=2, barcode="BOX-B-002", locationID=loc2.locationID
    )
    box6 = addBox(
        bayNo=1, rowNo=1, columnNo=1, barcode="BOX-C-001", locationID=loc3.locationID
    )

    # -------------------------------------------------------------------------
    # Files — Student type
    # -------------------------------------------------------------------------
    f1 = addFile(
        boxID=box1.boxID,
        fileType="Student",
        description="Undergraduate academic record – BSc Computer Science",
        previousDesignation="STU-2018-001",
        createdByStaffUserID=staff1.staffUserID,
        dateCreated=datetime(2018, 9, 3),
    )
    f2 = addFile(
        boxID=box1.boxID,
        fileType="Student",
        description="Postgraduate academic record – MSc Information Technology",
        previousDesignation="STU-2019-045",
        createdByStaffUserID=staff1.staffUserID,
        dateCreated=datetime(2019, 9, 2),
    )
    f3 = addFile(
        boxID=box2.boxID,
        fileType="Student",
        description="Undergraduate academic record – BSc Management Studies",
        previousDesignation="STU-2020-112",
        createdByStaffUserID=staff2.staffUserID,
        dateCreated=datetime(2020, 9, 7),
    )
    f4 = addFile(
        boxID=box2.boxID,
        fileType="Student",
        description="Undergraduate academic record – BSc Civil Engineering",
        previousDesignation="STU-2017-088",
        createdByStaffUserID=staff1.staffUserID,
        dateCreated=datetime(2017, 9, 4),
    )
    f5 = addFile(
        boxID=box3.boxID,
        fileType="Student",
        description="Part-time student record – Diploma in Business Administration",
        previousDesignation="STU-2021-033",
        createdByStaffUserID=staff2.staffUserID,
        dateCreated=datetime(2021, 1, 11),
    )

    # -------------------------------------------------------------------------
    # Files — Staff type
    # -------------------------------------------------------------------------
    f6 = addFile(
        boxID=box4.boxID,
        fileType="Staff",
        description="Administrative staff personnel file",
        previousDesignation="STF-2015-007",
        createdByStaffUserID=staff_admin.staffUserID,
        dateCreated=datetime(2015, 3, 16),
    )
    f7 = addFile(
        boxID=box4.boxID,
        fileType="Staff",
        description="Faculty academic personnel file – Lecturer",
        previousDesignation="STF-2016-023",
        createdByStaffUserID=staff_admin.staffUserID,
        dateCreated=datetime(2016, 8, 22),
    )
    f8 = addFile(
        boxID=box5.boxID,
        fileType="Staff",
        description="Senior administrative officer file",
        previousDesignation="STF-2013-004",
        createdByStaffUserID=staff1.staffUserID,
        dateCreated=datetime(2013, 6, 1),
    )
    f9 = addFile(
        boxID=box6.boxID,
        fileType="Staff",
        description="Transferred faculty file – off-site storage",
        previousDesignation="STF-2011-019",
        createdByStaffUserID=staff_admin.staffUserID,
        dateCreated=datetime(2011, 1, 17),
    )

    # -------------------------------------------------------------------------
    # Student file records
    # -------------------------------------------------------------------------
    create_student_record(
        fileID=f1.fileID,
        certificateDiploma="BSc Computer Science",
        code="SC-BSC-CS",
    )
    create_student_record(
        fileID=f2.fileID,
        certificateDiploma="MSc Information Technology",
        code="SC-MSC-IT",
    )
    create_student_record(
        fileID=f3.fileID,
        certificateDiploma="BSc Management Studies",
        code="FB-BSC-MS",
    )
    create_student_record(
        fileID=f4.fileID,
        certificateDiploma="BSc Civil Engineering",
        code="EN-BSC-CE",
    )
    create_student_record(
        fileID=f5.fileID,
        certificateDiploma="Diploma in Business Administration",
        code="FB-DIP-BA",
    )

    # -------------------------------------------------------------------------
    # Staff file records
    # -------------------------------------------------------------------------
    create_staff_record(
        fileID=f6.fileID,
        fileNumber="STF-007",
        fileTitle="Administrative Officer",
        post="Senior Administrator",
        organisationUnit="Registry",
        notes="Joined January 2015. Handles admissions records.",
    )
    create_staff_record(
        fileID=f7.fileID,
        fileNumber="STF-023",
        fileTitle="Lecturer I",
        post="Lecturer",
        organisationUnit="Department of Computing and Information Technology",
        notes="Joined September 2016. Research focus: distributed systems.",
    )
    create_staff_record(
        fileID=f8.fileID,
        fileNumber="STF-004",
        fileTitle="Senior Administrative Officer",
        post="Senior Administrative Officer",
        organisationUnit="Bursar's Office",
        notes="Joined June 2013. Transferred to Block B vault in 2018.",
    )
    create_staff_record(
        fileID=f9.fileID,
        fileNumber="STF-019",
        fileTitle="Associate Professor",
        post="Associate Professor",
        organisationUnit="Faculty of Engineering",
        notes="Joined January 2011. File transferred to offsite facility 2020.",
    )

    # -------------------------------------------------------------------------
    # Loans
    # -------------------------------------------------------------------------
    # Loan 1 – completed (returned)
    loan1 = create_loan(
        patronID=patron1.patronID,
        processedByStaffUserID=staff1.staffUserID,
        loanDate=datetime(2024, 2, 5),
    )
    return_loan(loan1.loanID, returnDate=datetime(2024, 2, 19))

    # Loan 2 – completed (returned)
    loan2 = create_loan(
        patronID=patron2.patronID,
        processedByStaffUserID=staff2.staffUserID,
        loanDate=datetime(2024, 5, 10),
    )
    return_loan(loan2.loanID, returnDate=datetime(2024, 5, 24))

    # Loan 3 – active (not yet returned)
    create_loan(
        patronID=patron3.patronID,
        processedByStaffUserID=staff1.staffUserID,
        loanDate=datetime(2025, 1, 20),
    )

    # Loan 4 – active (not yet returned)
    create_loan(
        patronID=patron4.patronID,
        processedByStaffUserID=staff_admin.staffUserID,
        loanDate=datetime(2025, 3, 3),
    )

    print("Database initialised with seed data.")
    print(f"  Locations : {len([loc1, loc2, loc3])}")
    print(f"  Boxes     : {len([box1, box2, box3, box4, box5, box6])}")
    print(f"  Staff     : {len([staff_admin, staff1, staff2])}")
    print(f"  Patrons   : {len([patron1, patron2, patron3, patron4])}")
    print(f"  Files     : 9  (5 student, 4 staff)")
    print(f"  Loans     : 4  (2 returned, 2 active)")
