from App.database import db


class StaffUser(db.Model):
    __tablename__ = 'staff_user'

    staffUserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)

    loans_processed = db.relationship(
        'Loan',
        backref='staff_user',
        lazy=True,
        foreign_keys='Loan.processedByStaffUserID'
    )
    files_created = db.relationship('File', backref='created_by_staff', lazy=True)

    def __repr__(self):
        return f'<StaffUser {self.staffUserID}>'