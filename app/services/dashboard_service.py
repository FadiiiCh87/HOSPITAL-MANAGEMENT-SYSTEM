from sqlalchemy import extract
import calendar
import datetime

from app.extensions import db

from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.department import Department
from app.models.appointment import Appointment
from app.models.medicine import Medicine
from app.models.laboratory import Laboratory
from app.models.bill import Bill

from app.utils.constants import (
    LOW_STOCK_LIMIT,
    APPOINTMENT_PENDING,
    APPOINTMENT_COMPLETED,
    APPOINTMENT_CANCELLED
)


def get_dashboard_data():
    doctor_count = Doctor.query.count()
    available_doctors = Doctor.query.count()
    bill_count = Bill.query.count()
    department_count = Department.query.count()
    patient_count = Patient.query.count()
    appointment_count = Appointment.query.count()
    medicine_count = Medicine.query.count()
    laboratory_count = Laboratory.query.count()

    pending_count = Appointment.query.filter_by(
        status=APPOINTMENT_PENDING
    ).count()

    completed_count = Appointment.query.filter_by(
        status=APPOINTMENT_COMPLETED
    ).count()

    cancelled_count = Appointment.query.filter_by(
        status=APPOINTMENT_CANCELLED
    ).count()

    recent_patients = (
        Patient.query
        .order_by(Patient.id.desc())
        .limit(5)
        .all()
    )

    recent_bills = (
        Bill.query
        .order_by(Bill.id.desc())
        .limit(5)
        .all()
    )

    today_appointments = (
        Appointment.query
        .order_by(Appointment.id.desc())
        .limit(5)
        .all()
    )

    low_stock_medicines = (
        Medicine.query
        .filter(
            Medicine.quantity <= LOW_STOCK_LIMIT
        )
        .all()
    )

    today = datetime.date.today()

    expired_medicines = (
        Medicine.query
        .filter(Medicine.expiry_date < today)
        .all()
    )

    bill_amount_column = (
        getattr(Bill, "amount", None)
        or getattr(Bill, "total_amount", None)
        or getattr(Bill, "total", None)
    )
    bill_date_column = (
        getattr(Bill, "date", None)
        or getattr(Bill, "bill_date", None)
        or getattr(Bill, "created_at", None)
    )
    appointment_date_column = (
        getattr(Appointment, "date", None)
        or getattr(Appointment, "appointment_date", None)
        or getattr(Appointment, "scheduled_date", None)
    )

    monthly_revenue = []
    months = []

    for month in range(1, 13):
        if bill_amount_column is not None and bill_date_column is not None:
            month_total = (
                Bill.query
                .with_entities(db.func.coalesce(db.func.sum(bill_amount_column), 0))
                .filter(extract("month", bill_date_column) == month)
                .scalar()
                or 0
            )
        else:
            month_total = 0

        monthly_revenue.append(float(month_total))
        months.append(calendar.month_name[month])

    if bill_amount_column is not None:
        total_revenue = (
            Bill.query
            .with_entities(db.func.coalesce(db.func.sum(bill_amount_column), 0))
            .scalar()
            or 0
        )
    else:
        total_revenue = 0

    if bill_amount_column is not None and bill_date_column is not None:
        today_filter = db.cast(bill_date_column, db.Date) == today
        today_bill_count = Bill.query.filter(today_filter).count()
        today_revenue = (
            Bill.query
            .with_entities(db.func.coalesce(db.func.sum(bill_amount_column), 0))
            .filter(today_filter)
            .scalar()
            or 0
        )
    else:
        today_bill_count = 0
        today_revenue = 0

    if appointment_date_column is not None:
        today_appointment_count = Appointment.query.filter(
            appointment_date_column == today
        ).count()
    else:
        today_appointment_count = 0


    

    return {
        "doctor_count": doctor_count,
        "department_count": department_count,
        "patient_count": patient_count,
        "appointment_count": appointment_count,
        "medicine_count": medicine_count,
        "pending_count": pending_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "recent_patients": recent_patients,
        "today_appointments": today_appointments,
        "recent_bills": recent_bills,
        "low_stock_medicines": low_stock_medicines,
        "expired_medicines": expired_medicines,
        "monthly_revenue": monthly_revenue,
        "months": months,
        "bill_count": bill_count,
        "total_revenue": float(total_revenue),
        "today_appointment_count": today_appointment_count,
        "today_bill_count": today_bill_count,
        "today_revenue": float(today_revenue),
        "laboratory_count": laboratory_count,
        "available_doctors": available_doctors,
    }
