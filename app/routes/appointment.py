from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required

from app.services.appointment_service import (
    get_appointments,
    get_appointment,
    get_patients,
    get_doctors,
    get_appointment_summary,
    create_appointment,
    update_appointment,
    delete_appointment
)
from flask import request, redirect, url_for, flash

appointment_bp = Blueprint("appointment", __name__)


# ======================================================
# Appointment List
# ======================================================

@appointment_bp.route("/appointments")
@login_required
def appointments():

    search = request.args.get("search", "").strip()

    status = request.args.get("status", "").strip()

    sort = request.args.get("sort", "latest")

    page = request.args.get("page", 1, type=int)

    appointments = get_appointments(
        search,
        status,
        sort,
        page
    )
    summary = get_appointment_summary()
    return render_template(
        "appointment/appointments.html",
        appointments=appointments,
        search=search,
        status=status,
        sort=sort,
        summary=summary
    )
# ======================================================
# Add Appointment
# ======================================================

@appointment_bp.route("/appointments/add", methods=["GET", "POST"])
@login_required
def add_appointment():

    patients = get_patients()
    doctors = get_doctors()

    if request.method == "POST":

        success, message = create_appointment(
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:

            return redirect(
                url_for("appointment.appointments")
            )

        return render_template(
            "appointment/add_appointment.html",
            patients=patients,
            doctors=doctors
        )

    return render_template(
        "appointment/add_appointment.html",
        patients=patients,
        doctors=doctors
    )
# ======================================================
# Edit Appointment
# ======================================================

@appointment_bp.route("/appointments/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_appointment(id):

    appointment = get_appointment(id)

    patients = get_patients()

    doctors = get_doctors()

    if request.method == "POST":

        update_appointment(
            appointment,
            request.form
        )

        flash(
            "Appointment Updated Successfully!",
            "success"
        )

        return redirect(
            url_for("appointment.appointments")
        )

    return render_template(
        "appointment/edit_appointment.html",
        appointment=appointment,
        patients=patients,
        doctors=doctors
    )
# ======================================================
# Delete Appointment
# ======================================================

@appointment_bp.route("/appointments/delete/<int:id>", methods=["POST"])
@login_required
def delete_appointment_route(id):

    appointment = get_appointment(id)

    delete_appointment(appointment)

    flash(
        "Appointment Deleted Successfully!",
        "success"
    )

    return redirect(
        url_for("appointment.appointments")
    )