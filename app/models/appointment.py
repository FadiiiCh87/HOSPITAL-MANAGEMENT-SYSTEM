from app.extensions import db


class Appointment(db.Model):

    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)

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

    appointment_date = db.Column(
        db.Date,
        nullable=False
    )

    appointment_time = db.Column(
        db.Time,
        nullable=False
    )

    duration_minutes = db.Column(db.Integer, nullable=False, default=30, server_default='30')

    reason = db.Column(
        db.Text
    )

    status = db.Column(
        db.String(30),
        default="Pending"
    )

    patient = db.relationship(
        "Patient",
        backref="appointments"
    )

    doctor = db.relationship(
        "Doctor",
        backref="appointments"
    )

from sqlalchemy import Index, text
Index("uq_active_doctor_slot", Appointment.doctor_id, Appointment.appointment_date, Appointment.appointment_time, unique=True, postgresql_where=text("status != 'Cancelled'"), sqlite_where=text("status != 'Cancelled'"))
