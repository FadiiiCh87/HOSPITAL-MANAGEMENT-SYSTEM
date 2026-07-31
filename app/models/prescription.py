from app.extensions import db


class Prescription(db.Model):

    __tablename__ = "prescriptions"

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

    diagnosis = db.Column(
        db.Text,
        nullable=False
    )

    medicines = db.Column(
        db.Text,
        nullable=False
    )

    notes = db.Column(
        db.Text
    )

    prescription_date = db.Column(
        db.Date,
        nullable=False
    )

    patient = db.relationship(
        "Patient",
        backref="prescriptions"
    )

    doctor = db.relationship(
        "Doctor",
        backref="prescriptions"
    )