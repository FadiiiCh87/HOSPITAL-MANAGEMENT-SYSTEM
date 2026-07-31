from sqlalchemy import and_
from sqlalchemy import or_
from datetime import datetime, date
from datetime import datetime
from app.extensions import db
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.doctor import Doctor


def get_appointments(search, status, sort, page):

    query = Appointment.query

    if status:

        query = query.filter(
            Appointment.status == status
        )

    if search:

        query = query.join(Patient).join(Doctor).filter(

            or_(

                Patient.full_name.ilike(f"%{search}%"),
                Doctor.full_name.ilike(f"%{search}%"),
                Appointment.reason.ilike(f"%{search}%")

            )

        )

    if sort == "latest":

        query = query.order_by(
            Appointment.id.desc()
        )

    elif sort == "oldest":

        query = query.order_by(
            Appointment.id.asc()
        )

    elif sort == "az":

        query = query.join(Patient).order_by(
            Patient.full_name.asc()
        )

    elif sort == "za":

        query = query.join(Patient).order_by(
            Patient.full_name.desc()
        )

    return query.paginate(
        page=page,
        per_page=5,
        error_out=False
    )


def get_appointment(id):

    return Appointment.query.get_or_404(id)


def get_patients():

    return Patient.query.all()


def get_doctors():

    return Doctor.query.all()



from datetime import datetime
from app.extensions import db
from app.models.appointment import Appointment


def create_appointment(form):

    doctor_id = int(form["doctor_id"])

    patient_id = int(form["patient_id"])

    appointment_date = datetime.strptime(
        form["appointment_date"],
        "%Y-%m-%d"
    ).date()

    appointment_time = datetime.strptime(
        form["appointment_time"],
        "%H:%M"
    ).time()

    # ---------------------------------------
    # Past Date Validation
    # ---------------------------------------

    if appointment_date < date.today():

        return (
            False,
            "Past dates are not allowed for appointments."
        )

    # ---------------------------------------
# Past Time Validation
# ---------------------------------------

    current_datetime = datetime.now()

    if (
        appointment_date == date.today()
        and appointment_time < current_datetime.time()
    ):

        return (
            False,
            "Selected appointment time has already passed."
        )

    

    reason = form["reason"]

    # ---------------------------------------
    # Check Doctor Double Booking
    # ---------------------------------------

    existing = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time
    ).first()

    if existing:

        return (
            False,
            "Doctor already has an appointment at this date and time."
        )

    appointment = Appointment(

        patient_id=patient_id,

        doctor_id=doctor_id,

        appointment_date=appointment_date,

        appointment_time=appointment_time,

        reason=reason

    )

    db.session.add(appointment)

    db.session.commit()

    return (
        True,
        "Appointment Added Successfully!"
    )



def update_appointment(appointment, form):

    appointment.patient_id = int(form["patient_id"])

    appointment.doctor_id = int(form["doctor_id"])

    appointment.appointment_date = datetime.strptime(
        form["appointment_date"],
        "%Y-%m-%d"
    ).date()

    appointment.appointment_time = datetime.strptime(
        form["appointment_time"],
        "%H:%M"
    ).time()

    appointment.reason = form["reason"]

    appointment.status = form["status"]

    db.session.commit()


def delete_appointment(appointment):

    db.session.delete(appointment)

    db.session.commit()


def get_appointment_summary():

    total = Appointment.query.count()

    pending = Appointment.query.filter_by(
        status="Pending"
    ).count()

    completed = Appointment.query.filter_by(
        status="Completed"
    ).count()

    cancelled = Appointment.query.filter_by(
        status="Cancelled"
    ).count()

    return {

        "total": total,

        "pending": pending,

        "completed": completed,

        "cancelled": cancelled

    }