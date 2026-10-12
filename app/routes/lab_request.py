from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required

from app.extensions import db

from datetime import date

from app.models.lab_request import LabRequest
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.laboratory import Laboratory

lab_request_bp = Blueprint(
    "lab_request",
    __name__
)





@lab_request_bp.route("/lab-requests")
@login_required
def lab_requests():

    search = request.args.get("search", "")

    query = LabRequest.query

    if search:

        query = (
            query
            .join(Patient)
            .filter(
                Patient.full_name.ilike(f"%{search}%")
            )
        )

    requests = (
        query
        .order_by(LabRequest.id.desc())
        .all()
    )

    return render_template(
        "lab_requests/lab_requests.html",
        requests=requests,
        search=search
    )
@lab_request_bp.route(
    "/lab-requests/result/<int:id>",
    methods=["GET", "POST"]
)


@login_required
def lab_result(id):

    request_data = LabRequest.query.get_or_404(id)

    if request.method == "POST":

        request_data.result = request.form["result"]

        request_data.status = request.form["status"]
        from app.models.portal import PublishedReport
        publication = PublishedReport.query.filter_by(lab_request_id=id).first()
        if publication:
            publication.published_at = None
            publication.file_data = None

        db.session.commit()

        flash(
            "Laboratory result updated successfully.",
            "success"
        )

        return redirect(
            url_for("lab_request.lab_requests")
        )

    return render_template(
        "lab_requests/lab_result.html",
        request_data=request_data
    )

@lab_request_bp.route("/lab-requests/print/<int:id>")
@login_required
def print_lab_report(id):

    request_data = LabRequest.query.get_or_404(id)

    return render_template(
        "lab_requests/print_lab_report.html",
        request_data=request_data
    )




@lab_request_bp.route(
    "/lab-requests/add",
    methods=["GET", "POST"]
)
@login_required
def add_lab_request():

    if request.method == "POST":

        lab_request = LabRequest(

            patient_id=request.form["patient_id"],

            doctor_id=request.form["doctor_id"],

            laboratory_id=request.form["laboratory_id"],

            request_date=date.today(),

            status="Pending"

        )

        db.session.add(lab_request)

        db.session.commit()

        flash(
            "Laboratory request created successfully.",
            "success"
        )

        return redirect(
            url_for("lab_request.lab_requests")
        )

    patients = Patient.query.order_by(
        Patient.full_name
    ).all()

    doctors = Doctor.query.order_by(
        Doctor.full_name
    ).all()

    tests = Laboratory.query.order_by(
        Laboratory.test_name
    ).all()

    return render_template(
        "lab_requests/add_lab_request.html",
        patients=patients,
        doctors=doctors,
        tests=tests
    )

# ======================================
# Delete Laboratory Request
# ======================================

@lab_request_bp.route(
    "/lab-requests/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_lab_request(id):

    request_data = LabRequest.query.get_or_404(id)

    db.session.delete(request_data)

    db.session.commit()

    flash(
        "Laboratory Request Deleted Successfully.",
        "success"
    )

    return redirect(
        url_for("lab_request.lab_requests")
    )