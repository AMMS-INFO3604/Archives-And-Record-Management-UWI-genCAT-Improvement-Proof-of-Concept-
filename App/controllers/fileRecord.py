from App.database import db
from App.models import StaffRecord, Student

# ---------------------------------------------------------------------------
# Student record CRUD
# ---------------------------------------------------------------------------


def create_student_record(fileID, certificateDiploma=None, code=None):
    record = Student(
        fileID=fileID,
        certificateDiploma=certificateDiploma,
        code=code,
    )
    try:
        db.session.add(record)
        db.session.commit()
        return record
    except Exception as e:
        db.session.rollback()
        print(f"Error creating student record: {e}")
        return None


def get_student_record(studentID):
    return db.session.get(Student, studentID)


def get_student_record_by_file(fileID):
    return db.session.execute(
        db.select(Student).filter_by(fileID=fileID)
    ).scalar_one_or_none()


def get_all_student_records():
    return db.session.scalars(db.select(Student)).all()


def update_student_record(studentID, certificateDiploma=None, code=None):
    record = get_student_record(studentID)
    if not record:
        print(f"Student record with ID {studentID} not found.")
        return None
    try:
        if certificateDiploma is not None:
            record.certificateDiploma = certificateDiploma
        if code is not None:
            record.code = code
        db.session.commit()
        return record
    except Exception as e:
        db.session.rollback()
        print(f"Error updating student record {studentID}: {e}")
        return None


def delete_student_record(studentID):
    record = get_student_record(studentID)
    if not record:
        print(f"Student record with ID {studentID} not found.")
        return False
    try:
        db.session.delete(record)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting student record {studentID}: {e}")
        return False


# ---------------------------------------------------------------------------
# Staff record CRUD
# ---------------------------------------------------------------------------


def create_staff_record(
    fileID,
    fileNumber=None,
    fileTitle=None,
    post=None,
    organisationUnit=None,
    notes=None,
):
    record = StaffRecord(
        fileID=fileID,
        fileNumber=fileNumber,
        fileTitle=fileTitle,
        post=post,
        organisationUnit=organisationUnit,
        notes=notes,
    )
    try:
        db.session.add(record)
        db.session.commit()
        return record
    except Exception as e:
        db.session.rollback()
        print(f"Error creating staff record: {e}")
        return None


def get_staff_record(staffRecordID):
    return db.session.get(StaffRecord, staffRecordID)


def get_staff_record_by_file(fileID):
    return db.session.execute(
        db.select(StaffRecord).filter_by(fileID=fileID)
    ).scalar_one_or_none()


def get_all_staff_records():
    return db.session.scalars(db.select(StaffRecord)).all()


def update_staff_record(
    staffRecordID,
    fileNumber=None,
    fileTitle=None,
    post=None,
    organisationUnit=None,
    notes=None,
):
    record = get_staff_record(staffRecordID)
    if not record:
        print(f"Staff record with ID {staffRecordID} not found.")
        return None
    try:
        if fileNumber is not None:
            record.fileNumber = fileNumber
        if fileTitle is not None:
            record.fileTitle = fileTitle
        if post is not None:
            record.post = post
        if organisationUnit is not None:
            record.organisationUnit = organisationUnit
        if notes is not None:
            record.notes = notes
        db.session.commit()
        return record
    except Exception as e:
        db.session.rollback()
        print(f"Error updating staff record {staffRecordID}: {e}")
        return None


def delete_staff_record(staffRecordID):
    record = get_staff_record(staffRecordID)
    if not record:
        print(f"Staff record with ID {staffRecordID} not found.")
        return False
    try:
        db.session.delete(record)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting staff record {staffRecordID}: {e}")
        return False
