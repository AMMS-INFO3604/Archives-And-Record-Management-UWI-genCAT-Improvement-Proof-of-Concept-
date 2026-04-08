from App.database import db

class Box(db.Model):
    __tablename__ = 'box'

    boxID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bayNo = db.Column(db.Integer, nullable=False)
    rowNo = db.Column(db.Integer, nullable=False)
    columnNo = db.Column(db.Integer, nullable=False)
    barcode = db.Column(db.String(100), unique=True, nullable=True)
    locationID = db.Column(db.Integer, db.ForeignKey('location.locationID'), nullable=False)
    colorStatus = db.Column(db.String(100), nullable=True)  # manually set status label

    files = db.relationship('File', backref='box', lazy=True)

    @property
    def color_status(self):
        """Return the manually set colorStatus if present, otherwise derive from file states."""
        if self.colorStatus:
            return self.colorStatus

        if not self.files:
            return "Unprocessed/Pending"

        status_set = set(f.status for f in self.files if f.status)

        mapping_check = [
            ("Unprocessed/Pending", "Unprocessed/Pending"),
            ("Missing File", "Missing File"),
            ("Damaged Records", "Damaged Records"),
            ("Action Required", "Action Required"),
            ("Unintentional Destruction (Disaster)", "Unintentional Destruction (Disaster)"),
            ("Approved/Authorised Destruction", "Approved/Authorised Destruction"),
            ("Pending Scanning", "Pending Scanning"),
            ("Scanned", "Scanned"),
        ]

        for key, value in mapping_check:
            if key in status_set:
                return value

        if "Available" in status_set and "On Loan" not in status_set:
            if len(self.files) >= 50:
                return "Full/Max Capacity"
            return "Space Available"

        if "On Loan" in status_set:
            return "Space Available"

        if len(self.files) >= 50:
            return "Full/Max Capacity"

        return "Space Available"

    def __repr__(self):
        return f'<Box {self.boxID}>'