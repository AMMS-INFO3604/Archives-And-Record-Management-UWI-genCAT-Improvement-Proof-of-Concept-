from werkzeug.security import check_password_hash, generate_password_hash

from App.database import db


class User(db.Model):
    __tablename__ = "user"

    userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)

    staff_profile = db.relationship(
        "StaffUser", backref="user", uselist=False, lazy=True
    )
    patron_profile = db.relationship("Patron", backref="user", uselist=False, lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def get_json(self):
        return {"id": self.userID, "username": self.username}

    def set_password(self, password):
        """Create hashed password."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check hashed password."""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<User {self.username}>"
