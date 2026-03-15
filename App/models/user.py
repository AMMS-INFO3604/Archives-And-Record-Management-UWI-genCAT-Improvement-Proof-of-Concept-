from App.database import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'user'

    userID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    userType = db.Column(db.Boolean, nullable=False, default=False)

    patron = db.relationship('Patron', backref='user', uselist=False)
    staff_user = db.relationship('StaffUser', backref='user', uselist=False)

    def __init__(self, username, password, userType=False):
        self.username = username
        self.password = generate_password_hash(password)
        self.userType = userType

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def get_json(self):
        return {
            "id": self.userID,
            "username": self.username
        }

    def __repr__(self):
        return f'<User {self.username}>'