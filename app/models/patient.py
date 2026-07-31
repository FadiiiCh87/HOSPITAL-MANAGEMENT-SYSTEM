from app.extensions import db


class Patient(db.Model):

    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100), nullable=False)

    age = db.Column(db.Integer)

    gender = db.Column(db.String(20))

    phone = db.Column(db.String(20))

    email = db.Column(db.String(100), unique=True)

    address = db.Column(db.Text)

    blood_group = db.Column(db.String(10))

    photo = db.Column(db.String(255))

    # Relationships
    bills = db.relationship(
        "Bill",
        back_populates="patient",
        cascade="all, delete-orphan"
    )