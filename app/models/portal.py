from datetime import datetime, timezone
from flask_login import UserMixin
from app.extensions import db

class PatientAccount(UserMixin, db.Model):
    __tablename__ = 'patient_accounts'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    token_version = db.Column(db.Integer, nullable=False, default=0)
    patient = db.relationship('Patient')
    role = 'Patient'
    def get_id(self): return f'patient:{self.id}:{self.token_version}'
    @property
    def full_name(self): return self.patient.full_name

class DoctorAccount(db.Model):
    __tablename__ = 'doctor_accounts'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), unique=True, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), unique=True, nullable=False)

class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedules'
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    slot_minutes = db.Column(db.Integer, nullable=False, default=30)
    doctor = db.relationship('Doctor')
    __table_args__ = (db.UniqueConstraint('doctor_id', 'weekday'),)

class Checkup(db.Model):
    __tablename__ = 'checkups'
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), unique=True, nullable=False)
    prescription_id = db.Column(db.Integer, db.ForeignKey('prescriptions.id'))
    diagnosis = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    follow_up = db.Column(db.Date)
    appointment = db.relationship('Appointment')

class PublishedReport(db.Model):
    __tablename__ = 'published_reports'
    id = db.Column(db.Integer, primary_key=True)
    lab_request_id = db.Column(db.Integer, db.ForeignKey('lab_requests.id'), unique=True, nullable=False)
    published_at = db.Column(db.DateTime)
    file_data = db.Column(db.LargeBinary)
    lab_request = db.relationship('LabRequest')

class AuditEvent(db.Model):
    __tablename__ = 'audit_events'
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(60), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
