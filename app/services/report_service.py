from sqlalchemy import func

from app.extensions import db
from app.models.bill import Bill
from app.models.appointment import Appointment


# ==========================================
# Revenue Report
# ==========================================

def get_revenue_report(from_date=None, to_date=None):

    total_revenue = db.session.query(
        func.sum(Bill.total_amount)
    ).scalar() or 0

    paid_revenue = db.session.query(
        func.sum(Bill.total_amount)
    ).filter(
        Bill.payment_status == "Paid"
    ).scalar() or 0

    unpaid_revenue = db.session.query(
        func.sum(Bill.total_amount)
    ).filter(
        Bill.payment_status == "Unpaid"
    ).scalar() or 0

    total_bills = Bill.query.count()

    query = Bill.query

    if from_date:
        query = query.filter(
            Bill.created_at >= from_date
        )

    if to_date:
        query = query.filter(
            Bill.created_at <= to_date
        )

    bills = (
        query
        .order_by(Bill.created_at.desc())
        .all()
    )

    return {
        "total_revenue": total_revenue,
        "paid_revenue": paid_revenue,
        "unpaid_revenue": unpaid_revenue,
        "total_bills": total_bills,
        "bills": bills,
    }


# ==========================================
# Appointment Report
# ==========================================

def get_appointment_report(from_date=None, to_date=None):

    total_appointments = Appointment.query.count()

    pending_count = Appointment.query.filter_by(
        status="Pending"
    ).count()

    completed_count = Appointment.query.filter_by(
        status="Completed"
    ).count()

    cancelled_count = Appointment.query.filter_by(
        status="Cancelled"
    ).count()

    query = Appointment.query

    if from_date:
        query = query.filter(
            Appointment.appointment_date >= from_date
        )

    if to_date:
        query = query.filter(
            Appointment.appointment_date <= to_date
        )

    appointments = (
        query
        .order_by(Appointment.appointment_date.desc())
        .all()
    )

    return {
        "total_appointments": total_appointments,
        "pending_count": pending_count,
        "completed_count": completed_count,
        "cancelled_count": cancelled_count,
        "appointments": appointments,
    }


# ==========================================
# Excel / PDF
# ==========================================

def get_all_appointments():

    return (
        Appointment.query
        .order_by(
            Appointment.appointment_date.desc()
        )
        .all()
    )