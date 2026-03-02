from App.database import db


class Student(db.Model):
    __tablename__ = 'student'

    studentID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    certificateDiploma = db.Column(db.String(255), nullable=True)
    code = db.Column(db.String(100), nullable=True)
    fileID = db.Column(db.Integer, db.ForeignKey('file.fileID'), nullable=False)

    def __repr__(self):
        return f'<Student {self.studentID}>'


class StaffRecord(db.Model):
    __tablename__ = 'staff_record'

    staffRecordID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fileNumber = db.Column(db.String(100), nullable=True)
    fileTitle = db.Column(db.String(255), nullable=True)
    post = db.Column(db.String(255), nullable=True)
    organisationUnit = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    fileID = db.Column(db.Integer, db.ForeignKey('file.fileID'), nullable=False)

    def __repr__(self):
        return f'<StaffRecord {self.staffRecordID}>'