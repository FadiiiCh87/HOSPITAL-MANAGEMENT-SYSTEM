from app.extensions import db


class LabRequest(db.Model):

    __tablename__ = "lab_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctors.id"),
        nullable=False
    )

    laboratory_id = db.Column(
        db.Integer,
        db.ForeignKey("laboratory.id"),
        nullable=False
    )

    request_date = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    result = db.Column(
        db.Text
    )

    patient = db.relationship(
        "Patient",
        backref="lab_requests"
    )

    doctor = db.relationship(
        "Doctor",
        backref="lab_requests"
    )

    laboratory = db.relationship(
        "Laboratory",
        backref="lab_requests"
    )