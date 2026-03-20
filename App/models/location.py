from App.database import db


class Location(db.Model):
    __tablename__ = "location"

    locationID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    geoLocation = db.Column(db.String(255), nullable=False)
    campus = db.Column(db.String(255), nullable=True) # e.g. "St. Augustine", "Debe"

    boxes = db.relationship("Box", backref="location", lazy=True)

    @property
    def file_count(self):
        count = 0
        for box in self.boxes:
            count += len(box.files)
        return count

    def get_json(self):
        return {
            "locationID": self.locationID,
            "geoLocation": self.geoLocation,
            "campus": self.campus
        }

    def __repr__(self):
        return f"<Location {self.geoLocation}>"
