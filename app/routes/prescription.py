from app.services.prescription_service import (
    get_prescriptions,
    get_prescription,
    get_patients,
    get_doctors,
    create_prescription,
    update_prescription,
    delete_prescription_record
)

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required


prescription_bp = Blueprint(
    "prescription",
    __name__
)


@prescription_bp.route("/prescriptions")
@login_required
def prescriptions():

    search = request.args.get("search", "").strip()

    prescriptions = get_prescriptions(
    search
)

    
    return render_template(
        "prescriptions/prescriptions.html",
        prescriptions=prescriptions,
        search=search
    )


@prescription_bp.route(
    "/prescriptions/add",
    methods=["GET", "POST"]
)
@login_required
def add_prescription():

    patients = get_patients()

    doctors = get_doctors()

    if request.method == "POST":

        success, message = create_prescription(
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        return redirect(
            url_for("prescription.prescriptions")
        )

    return render_template(
        "prescriptions/add_prescription.html",
        patients=patients,
        doctors=doctors
    )

# ======================================================
# Edit Prescription
# ======================================================

@prescription_bp.route(
    "/prescriptions/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_prescription(id):

    prescription = get_prescription(id)

    patients = get_patients()

    doctors = get_doctors()

    if request.method == "POST":

        success, message = update_prescription(
            prescription,
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        return redirect(
            url_for("prescription.prescriptions")
        )

    return render_template(
        "prescriptions/edit_prescription.html",
        prescription=prescription,
        patients=patients,
        doctors=doctors
    )

@prescription_bp.route("/prescriptions/view/<int:id>")
@login_required
def view_prescription(id):
    prescription = get_prescription(id)

    return render_template(
        "prescriptions/view_prescription.html",
        prescription=prescription
    )

@prescription_bp.route("/prescriptions/print/<int:id>")
@login_required
def print_prescription(id):

    prescription = get_prescription(id)
    return render_template(
        "prescriptions/print_prescription.html",
        prescription=prescription
    )

# ======================================================
# Delete Prescription
# ======================================================

@prescription_bp.route(
    "/prescriptions/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_prescription(id):

    prescription = get_prescription(id)

    success, message = delete_prescription_record(
        prescription
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("prescription.prescriptions")
    )

