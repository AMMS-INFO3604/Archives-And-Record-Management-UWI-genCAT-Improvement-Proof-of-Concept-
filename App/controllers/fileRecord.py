from App.database import db
from App.models import File, StaffRecord, Student

# ---------------------------------------------------------------------------
# Student – Create
# ---------------------------------------------------------------------------


def create_student_record(fileID, certificateDiploma=None, code=None):
    """Create a Student record linked to an existing File.

    Args:
        fileID: The ID of the File this student record belongs to.
        certificateDiploma: Optional certificate or diploma name.
        code: Optional student/programme code.

    Returns:
        The new Student instance, or None on failure.
    """
    file = db.session.get(File, fileID)
    if not file:
        print(f"File with ID {fileID} not found.")
        return None

    existing = get_student_record_by_file(fileID)
    if existing:
        print(f"A Student record already exists for file {fileID}.")
        return None

    student = Student(
        fileID=fileID,
        certificateDiploma=certificateDiploma,
        code=code,
    )
    try:
        db.session.add(student)
        db.session.commit()
        return student
    except Exception as e:
        db.session.rollback()
        print(f"Error creating student record: {e}")
        return None


# ---------------------------------------------------------------------------
# Student – Read
# ---------------------------------------------------------------------------


def get_student_record(studentID):
    """Return a Student record by its primary key."""
    return db.session.get(Student, studentID)


def get_student_record_by_file(fileID):
    """Return the Student record associated with a given fileID."""
    return db.session.execute(
        db.select(Student).filter_by(fileID=fileID)
    ).scalar_one_or_none()


def get_student_record_json(studentID):
    student = get_student_record(studentID)
    if not student:
        return None
    return _student_to_dict(student)


def get_all_student_records():
    return db.session.scalars(db.select(Student)).all()


def get_all_student_records_json():
    return [_student_to_dict(s) for s in get_all_student_records()]


def search_student_records(code=None, certificateDiploma=None):
    """Search Student records by code and/or certificateDiploma (case-insensitive
    partial match).

    Returns:
        A list of matching Student instances.
    """
    query = db.select(Student)
    if code:
        query = query.where(Student.code.ilike(f"%{code}%"))
    if certificateDiploma:
        query = query.where(Student.certificateDiploma.ilike(f"%{certificateDiploma}%"))
    return db.session.scalars(query).all()


def search_student_records_json(code=None, certificateDiploma=None):
    return [
        _student_to_dict(s)
        for s in search_student_records(
            code=code, certificateDiploma=certificateDiploma
        )
    ]


# ---------------------------------------------------------------------------
# Student – Update
# ---------------------------------------------------------------------------


def update_student_record(studentID, certificateDiploma=None, code=None):
    """Update a Student record.  Only supplied (non-None) fields are changed."""
    student = get_student_record(studentID)
    if not student:
        print(f"Student record with ID {studentID} not found.")
        return None

    try:
        if certificateDiploma is not None:
            student.certificateDiploma = certificateDiploma
        if code is not None:
            student.code = code
        db.session.commit()
        return student
    except Exception as e:
        db.session.rollback()
        print(f"Error updating student record {studentID}: {e}")
        return None


# ---------------------------------------------------------------------------
# Student – Delete
# ---------------------------------------------------------------------------


def delete_student_record(studentID):
    """Delete a Student record by its primary key."""
    student = get_student_record(studentID)
    if not student:
        print(f"Student record with ID {studentID} not found.")
        return False
    try:
        db.session.delete(student)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting student record {studentID}: {e}")
        return False


# ---------------------------------------------------------------------------
# StaffRecord – Create
# ---------------------------------------------------------------------------


def create_staff_record(
    fileID,
    fileNumber=None,
    fileTitle=None,
    post=None,
    organisationUnit=None,
    notes=None,
):
    """Create a StaffRecord linked to an existing File.

    Args:
        fileID: The ID of the File this staff record belongs to.
        fileNumber: Optional reference file number.
        fileTitle: Optional title of the file.
        post: Optional post/job title held by the staff member.
        organisationUnit: Optional organisational unit.
        notes: Optional freeform notes.

    Returns:
        The new StaffRecord instance, or None on failure.
    """
    file = db.session.get(File, fileID)
    if not file:
        print(f"File with ID {fileID} not found.")
        return None

    existing = get_staff_record_by_file(fileID)
    if existing:
        print(f"A StaffRecord already exists for file {fileID}.")
        return None

    staff_record = StaffRecord(
        fileID=fileID,
        fileNumber=fileNumber,
        fileTitle=fileTitle,
        post=post,
        organisationUnit=organisationUnit,
        notes=notes,
    )
    try:
        db.session.add(staff_record)
        db.session.commit()
        return staff_record
    except Exception as e:
        db.session.rollback()
        print(f"Error creating staff record: {e}")
        return None


# ---------------------------------------------------------------------------
# StaffRecord – Read
# ---------------------------------------------------------------------------


def get_staff_record(staffRecordID):
    """Return a StaffRecord by its primary key."""
    return db.session.get(StaffRecord, staffRecordID)


def get_staff_record_by_file(fileID):
    """Return the StaffRecord associated with a given fileID."""
    return db.session.execute(
        db.select(StaffRecord).filter_by(fileID=fileID)
    ).scalar_one_or_none()


def get_staff_record_json(staffRecordID):
    staff_record = get_staff_record(staffRecordID)
    if not staff_record:
        return None
    return _staff_record_to_dict(staff_record)


def get_all_staff_records():
    return db.session.scalars(db.select(StaffRecord)).all()


def get_all_staff_records_json():
    return [_staff_record_to_dict(sr) for sr in get_all_staff_records()]


def search_staff_records(
    fileNumber=None,
    fileTitle=None,
    post=None,
    organisationUnit=None,
):
    """Search StaffRecords by any combination of fields (case-insensitive
    partial match).

    Returns:
        A list of matching StaffRecord instances.
    """
    query = db.select(StaffRecord)
    if fileNumber:
        query = query.where(StaffRecord.fileNumber.ilike(f"%{fileNumber}%"))
    if fileTitle:
        query = query.where(StaffRecord.fileTitle.ilike(f"%{fileTitle}%"))
    if post:
        query = query.where(StaffRecord.post.ilike(f"%{post}%"))
    if organisationUnit:
        query = query.where(StaffRecord.organisationUnit.ilike(f"%{organisationUnit}%"))
    return db.session.scalars(query).all()


def search_staff_records_json(
    fileNumber=None,
    fileTitle=None,
    post=None,
    organisationUnit=None,
):
    return [
        _staff_record_to_dict(sr)
        for sr in search_staff_records(
            fileNumber=fileNumber,
            fileTitle=fileTitle,
            post=post,
            organisationUnit=organisationUnit,
        )
    ]


# ---------------------------------------------------------------------------
# StaffRecord – Update
# ---------------------------------------------------------------------------


def update_staff_record(
    staffRecordID,
    fileNumber=None,
    fileTitle=None,
    post=None,
    organisationUnit=None,
    notes=None,
):
    """Update a StaffRecord.  Only supplied (non-None) fields are changed."""
    staff_record = get_staff_record(staffRecordID)
    if not staff_record:
        print(f"StaffRecord with ID {staffRecordID} not found.")
        return None

    try:
        if fileNumber is not None:
            staff_record.fileNumber = fileNumber
        if fileTitle is not None:
            staff_record.fileTitle = fileTitle
        if post is not None:
            staff_record.post = post
        if organisationUnit is not None:
            staff_record.organisationUnit = organisationUnit
        if notes is not None:
            staff_record.notes = notes
        db.session.commit()
        return staff_record
    except Exception as e:
        db.session.rollback()
        print(f"Error updating staff record {staffRecordID}: {e}")
        return None


# ---------------------------------------------------------------------------
# StaffRecord – Delete
# ---------------------------------------------------------------------------


def delete_staff_record(staffRecordID):
    """Delete a StaffRecord by its primary key."""
    staff_record = get_staff_record(staffRecordID)
    if not staff_record:
        print(f"StaffRecord with ID {staffRecordID} not found.")
        return False
    try:
        db.session.delete(staff_record)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting staff record {staffRecordID}: {e}")
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _student_to_dict(student):
    return {
        "studentID": student.studentID,
        "certificateDiploma": student.certificateDiploma,
        "code": student.code,
        "fileID": student.fileID,
    }


def _staff_record_to_dict(staff_record):
    return {
        "staffRecordID": staff_record.staffRecordID,
        "fileNumber": staff_record.fileNumber,
        "fileTitle": staff_record.fileTitle,
        "post": staff_record.post,
        "organisationUnit": staff_record.organisationUnit,
        "notes": staff_record.notes,
        "fileID": staff_record.fileID,
    }
