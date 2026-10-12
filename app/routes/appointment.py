from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required, current_user
from flask import abort
from app.extensions import db
from app.models.appointment import Appointment

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


@appointment_bp.post("/appointments/<int:id>/review")
@login_required
def review_request(id):
    if current_user.role not in {"Admin", "Receptionist"}:
        abort(403)
    decision = request.form.get("decision")
    if decision not in {"Confirmed", "Rejected"}:
        abort(400)
    from app.portal import lock_doctor, available, audit
    appointment = db.get_or_404(Appointment, id)
    lock_doctor(appointment.doctor_id)
    appointment = Appointment.query.filter_by(id=id).populate_existing().with_for_update().first_or_404()
    if appointment.status != "Pending":
        abort(409, description="This request has already been reviewed or cancelled. Refresh the list.")
    if decision == "Confirmed" and appointment.appointment_time.strftime("%H:%M") not in available(appointment.doctor_id, appointment.appointment_date, appointment.id):
        flash("This slot is no longer available. Contact the patient to select another time or reject the request.", "warning")
        return redirect(url_for("appointment.appointments", status="Pending"))
    if decision == "Confirmed":
        from app.models.portal import DoctorSchedule
        appointment.duration_minutes = DoctorSchedule.query.filter_by(doctor_id=appointment.doctor_id, weekday=appointment.appointment_date.weekday()).one().slot_minutes
    appointment.status = decision
    audit("appointment_" + decision.lower(), id)
    db.session.commit()
    flash(f"Appointment #{id} {decision.lower()}. The patient can see the update in their dashboard.", "success")
    return redirect(url_for("appointment.appointments", status="Pending"))


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
