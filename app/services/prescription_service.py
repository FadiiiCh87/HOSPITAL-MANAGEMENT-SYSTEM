from datetime import date

from sqlalchemy import or_

from app.extensions import db
from app.models.prescription import Prescription
from app.models.patient import Patient
from app.models.doctor import Doctor


# ======================================================
# Prescription List
# ======================================================

def get_prescriptions(search):

    query = Prescription.query

    if search:

        query = (
            query
            .join(Patient)
            .filter(
                Patient.full_name.ilike(f"%{search}%")
            )
        )

    return (
        query
        .order_by(Prescription.id.desc())
        .all()
    )


# ======================================================
# Single Prescription
# ======================================================

def get_prescription(id):

    return Prescription.query.get_or_404(id)


# ======================================================
# Patients
# ======================================================

def get_patients():

    return (
        Patient.query
        .order_by(Patient.full_name)
        .all()
    )


# ======================================================
# Doctors
# ======================================================

def get_doctors():

    return (
        Doctor.query
        .order_by(Doctor.full_name)
        .all()
    )


# ======================================================
# Create Prescription
# ======================================================

def create_prescription(form):

    prescription = Prescription(

        patient_id=int(form["patient_id"]),

        doctor_id=int(form["doctor_id"]),

        diagnosis=form["diagnosis"],

        medicines=form["medicines"],

        notes=form["notes"],

        prescription_date=date.today()

    )

    db.session.add(prescription)

    db.session.commit()

    return True, "Prescription added successfully."


# ======================================================
# Update Prescription
# ======================================================

def update_prescription(
    prescription,
    form
):

    prescription.patient_id = int(
        form["patient_id"]
    )

    prescription.doctor_id = int(
        form["doctor_id"]
    )

    prescription.diagnosis = form["diagnosis"]

    prescription.medicines = form["medicines"]

    prescription.notes = form["notes"]

    db.session.commit()

    return True, "Prescription updated successfully."


# ======================================================
# Delete Prescription
# ======================================================

def delete_prescription_record(
    prescription
):

    db.session.delete(
        prescription
    )

    db.session.commit()

    return True, "Prescription deleted successfully."