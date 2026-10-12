from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from app.models import bill
from flask_login import login_required
from app.services.billing_service import (
    get_all_bills,
    get_patients,
    get_bill,
    create_bill,
    update_bill,
    delete_bill_record
)

billing_bp = Blueprint("billing", __name__)


# ==========================
# Bills List
# ==========================
@billing_bp.route("/billing")
@login_required
def bills():
    search = request.args.get("search", "").strip()

    status = request.args.get("status", "").strip()

    sort = request.args.get("sort", "latest")

    page = request.args.get("page", 1, type=int)

    bills = get_all_bills(
        search,
        status,
        sort,
        page
    )

    return render_template(

        "billing/bills.html",

        bills=bills,

        search=search,

        status=status,

        sort=sort

    )
# ==========================
# Add Bill
# ==========================
@billing_bp.route("/billing/add", methods=["GET", "POST"])
@login_required
def add_bill():

    patients = get_patients()

    if request.method == "POST":

        success, message = create_bill(
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        return redirect(
            url_for("billing.bills")
        )

    return render_template(
        "billing/add_bill.html",
        patients=patients
    )

    
# ==========================
# View Bill
# ==========================
@billing_bp.route("/billing/view/<int:id>")
@login_required
def view_bill(id):

    bill = get_bill(id)

    return render_template(
        "billing/view_bill.html",
        bill=bill
    )
# ==========================
# Edit Bill
# ==========================
@billing_bp.route("/billing/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_bill(id):

    bill = get_bill(id)

    patients = get_patients()

    if request.method == "POST":

        success, message = update_bill(
            bill,
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
    )

        return redirect(
            url_for("billing.bills")
        )

    return render_template(
        "billing/edit_bill.html",
        bill=bill,
        patients=patients
    )
# ==========================
# Delete Bill
# ==========================
@billing_bp.route("/billing/delete/<int:id>", methods=["POST"])
@login_required
def delete_bill(id):
    bill = get_bill(id)
    success, message = delete_bill_record(
        bill
    )

    flash(
        message,
        "success" if success else "danger"
    )
   

    return redirect(
        url_for("billing.bills")
    )
# ==========================
# Print Invoice
# ==========================
@billing_bp.route("/billing/invoice/<int:id>")
@login_required
def print_invoice(id):

    bill = get_bill(id)

    return render_template(
        "billing/invoice.html",
        bill=bill
    )
