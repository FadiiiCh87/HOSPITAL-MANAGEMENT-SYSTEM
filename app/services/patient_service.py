from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.patient import Patient


def get_patients(search, page):

    query = Patient.query

    if search:

        query = query.filter(

            or_(

                Patient.full_name.ilike(f"%{search}%"),

                Patient.email.ilike(f"%{search}%"),

                Patient.phone.ilike(f"%{search}%"),

                Patient.blood_group.ilike(f"%{search}%")

            )

        )

    return query.paginate(

        page=page,

        per_page=5,

        error_out=False

    )


def get_patient(id):

    return Patient.query.get_or_404(id)

def create_patient(form):

    full_name = form["full_name"]
    age = int(form["age"])
    gender = form["gender"]
    phone = form["phone"]
    email = form["email"]
    blood_group=form["blood_group"]
    address = form["address"]

    existing = Patient.query.filter_by(
        email=email
    ).first()

    if existing:
        return False, "Patient email already exists."

    patient = Patient(
        full_name=full_name,
        age=age,
        gender=gender,
        phone=phone,
        email=email,
        blood_group=blood_group,
        address=address
    )

    db.session.add(patient)
    db.session.commit()

    return True, "Patient Added Successfully!"


def update_patient(patient, form):

    patient.full_name = form["full_name"]
    patient.age = int(form["age"])
    patient.gender = form["gender"]
    patient.phone = form["phone"]
    patient.email = form["email"]
    patient.blood_group = form["blood_group"]
    patient.address = form["address"]

    existing = Patient.query.filter(
        Patient.email == patient.email,
        Patient.id != patient.id
    ).first()

    if existing:
        return False, "Patient email already exists."

    db.session.commit()

    return True, "Patient Updated Successfully!"


def delete_patient_record(patient):

    try:

        db.session.delete(patient)
        db.session.commit()

        return True, "Patient Deleted Successfully!"

    except IntegrityError:

        db.session.rollback()

        return False, (
            "Cannot delete patient because related records "
            "(Bills, Appointments, Prescriptions, etc.) already exist."
        )