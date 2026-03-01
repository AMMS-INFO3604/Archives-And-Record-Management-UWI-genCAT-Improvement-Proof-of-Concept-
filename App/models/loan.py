from App.database import db
from datetime import datetime


class Loan(db.Model):
    __tablename__ = 'loan'

    loanID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    loanDate = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    returnDate = db.Column(db.DateTime, nullable=True)
    processedByStaffUserID = db.Column(
        db.Integer, db.ForeignKey('staff_user.staffUserID'), nullable=True
    )
    patronID = db.Column(db.Integer, db.ForeignKey('patron.patronID'), nullable=False)

    files = db.relationship('File', backref='loan', lazy=True)

    def __repr__(self):
        return f'<Loan {self.loanID}>'