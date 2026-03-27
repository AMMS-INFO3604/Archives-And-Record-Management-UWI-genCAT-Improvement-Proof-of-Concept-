from App.database import db
from datetime import datetime


class File(db.Model):
    __tablename__ = 'file'

    fileID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    boxID = db.Column(db.Integer, db.ForeignKey('box.boxID'), nullable=False)
    locationID = db.Column(db.Integer, db.ForeignKey('location.locationID'), nullable=True)
    loanID = db.Column(db.Integer, db.ForeignKey('loan.loanID'), nullable=True)
    fileType = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    previousDesignation = db.Column(db.String(255), nullable=True)
    createdByStaffUserID = db.Column(
        db.Integer, db.ForeignKey('staff_user.staffUserID'), nullable=True
    )
    dateCreated = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Available')

    student_record = db.relationship('Student', backref='file', uselist=False)
    staff_record = db.relationship('StaffRecord', backref='file', uselist=False)
    
    conditionNotes = db.Column(db.Text, nullable=True)
    barcode = db.Column(db.String(100), unique=True, nullable=True)

    def __repr__(self):
        return f'<File {self.fileID} - {self.fileType}>'