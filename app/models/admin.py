from flask_login import UserMixin
from app.extensions import db


class Admin(UserMixin, db.Model):

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)
    role = db.Column(
    db.String(30),
    nullable=False,
    default="Admin"
)