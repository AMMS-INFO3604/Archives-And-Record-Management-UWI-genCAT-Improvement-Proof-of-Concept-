from App.database import db


class Location(db.Model):
    __tablename__ = "location"

    locationID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    geoLocation = db.Column(db.String(255), nullable=False)

    boxes = db.relationship("Box", backref="location", lazy=True)

    def get_json(self):
        return {
            "locationID": self.locationID,
            "geoLocation": self.geoLocation,
        }

    def __repr__(self):
        return f"<Location {self.geoLocation}>"
