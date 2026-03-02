from App.database import db


class Box(db.Model):
    __tablename__ = 'box'

    boxID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bayNo = db.Column(db.Integer, nullable=False)
    rowNo = db.Column(db.Integer, nullable=False)
    columnNo = db.Column(db.Integer, nullable=False)
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    locationID = db.Column(db.Integer, db.ForeignKey('location.locationID'), nullable=False)

    files = db.relationship('File', backref='box', lazy=True)

    def __repr__(self):
        return f'<Box {self.boxID}>'