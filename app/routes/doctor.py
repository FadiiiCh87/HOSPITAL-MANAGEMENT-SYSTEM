from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)
from app.services.doctor_service import (
    get_doctors,
    get_doctor,
    get_departments,
    create_doctor,
    update_doctor,
    delete_doctor_record
)
from flask_login import login_required

doctor_bp = Blueprint("doctor", __name__)

# ======================================================
# Doctors List
# ======================================================
@doctor_bp.route("/doctors")
@login_required
def doctors():

    search = request.args.get("search", "").strip()

    department = request.args.get("department", "").strip()

    sort = request.args.get("sort", "latest")

    page = request.args.get("page", 1, type=int)

    doctors = get_doctors(
        search,
        department,
        sort,
        page
    )

    departments = get_departments()

    return render_template(
        "doctor/doctors.html",
        doctors=doctors,
        departments=departments,
        search=search,
        selected_department=department,
        sort=sort
    ) 
 
# ======================================================
# Add Doctor
# ======================================================

@doctor_bp.route("/doctors/add", methods=["GET", "POST"])
@login_required
def add_doctor():

    departments = get_departments()

    if request.method == "POST":

        success, message = create_doctor(
            request.form,
            request.files
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:
            return redirect(
                url_for("doctor.doctors")
            )

        return redirect(
            url_for("doctor.add_doctor")
        )

    return render_template(
        "doctor/add_doctor.html",
        departments=departments
    )

# ======================================================
# Edit Doctor
# ======================================================

@doctor_bp.route("/doctors/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_doctor(id):

    doctor = get_doctor(id)

    departments = get_departments()

    if request.method == "POST":

        success, message = update_doctor(
            doctor,
            request.form,
            request.files
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:
            return redirect(
                url_for("doctor.doctors")
            )

        return redirect(
            url_for(
                "doctor.edit_doctor",
                id=id
            )
        )

    return render_template(
        "doctor/edit_doctor.html",
        doctor=doctor,
        departments=departments
    )
# ======================================================
# Delete Doctor
# ======================================================

@doctor_bp.route("/doctors/delete/<int:id>", methods=["POST"])
@login_required
def delete_doctor(id):

    doctor = get_doctor(id)
    success, message = delete_doctor_record(doctor)

    flash(
        message,
        "success" if success else "danger"
    )
    

    return redirect(
        url_for("doctor.doctors")
    )