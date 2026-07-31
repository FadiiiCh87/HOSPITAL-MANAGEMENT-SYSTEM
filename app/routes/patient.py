from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from app.models import patient
from flask_login import login_required
from app.services.patient_service import (
    get_patients,
    get_patient, create_patient,
    update_patient,
    delete_patient_record
)

patient_bp = Blueprint("patient", __name__)


# ======================================================
# Patients List
# ======================================================
@patient_bp.route("/patients")
@login_required
def patients():

    search = request.args.get("search", "").strip()

    page = request.args.get("page", 1, type=int)

    patients = get_patients(
        search,
        page
    )

    return render_template(
        "patient/patients.html",
        patients=patients,
        search=search
    )

# ======================================================
# Add Patient
# ======================================================

@patient_bp.route("/patients/add", methods=["GET", "POST"])
@login_required
def add_patient():

    if request.method == "POST":

        success, message = create_patient(request.form)

        flash(
            message,
            "success" if success else "danger"
        )

        if success:
            return redirect(url_for("patient.patients"))

        return redirect(url_for("patient.add_patient"))

    return render_template(
        "patient/add_patient.html"
    )
        

# ======================================================
# Edit Patient
# ======================================================

@patient_bp.route("/patients/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_patient(id):

    patient = get_patient(id)

    if request.method == "POST":

        success, message = update_patient(
            patient,
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:
            return redirect(
                url_for("patient.patients")
            )

        return redirect(
            url_for(
                "patient.edit_patient",
                id=id
            )
        )

    return render_template(
        "patient/edit_patient.html",
        patient=patient
    )
    
    
# ======================================================
# Delete Patient
# ======================================================
@patient_bp.route("/patients/delete/<int:id>", methods=["POST"])
@login_required
def delete_patient(id):

    patient = get_patient(id)

    success, message = delete_patient_record(patient)

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("patient.patients")
    )