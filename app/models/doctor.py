from app.extensions import db

class Doctor(db.Model):

    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(100))

    specialization = db.Column(db.String(100))

    phone = db.Column(db.String(20))

    email = db.Column(db.String(100))

    gender = db.Column(db.String(20))

    experience = db.Column(db.Integer)

    photo = db.Column(db.String(255))

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id")
    )
    department = db.relationship(
    "Department",
    backref="doctors"
)
