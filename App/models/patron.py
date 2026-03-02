from App.database import db


class Patron(db.Model):
    __tablename__ = 'patron'

    patronID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)

    loans = db.relationship('Loan', backref='patron', lazy=True)

    def __repr__(self):
        return f'<Patron {self.patronID}>'