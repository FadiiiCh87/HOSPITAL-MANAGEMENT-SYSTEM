from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import login_required

from app.services.medicine_service import (
    get_medicines,
    get_medicine,
    create_medicine,
    update_medicine,
    delete_medicine_record,
    get_today,
    get_categories,
    get_medicine_statistics
)


medicine_bp = Blueprint("medicine", __name__)


# =====================================
# Medicines List
# =====================================

@medicine_bp.route("/medicines")
@login_required
def medicines():

    search = request.args.get("search", "").strip()

    sort = request.args.get("sort", "latest")

    filter_by = request.args.get("filter", "")

    page = request.args.get("page", 1, type=int)

    stats = get_medicine_statistics()

    filter_by = request.args.get(
    "filter",
    ""
)

    medicines = get_medicines(
        search,
        sort,
        filter_by
    )

    return render_template(

        "medicine/medicines.html",

        medicines=medicines,

        search=search,

        stats=stats,

        sort=sort,

        filter_by=filter_by,

        today=get_today(),

        

    )

        
    

 
# =====================================
# Add Medicine
# =====================================

@medicine_bp.route("/medicines/add", methods=["GET", "POST"])
@login_required
def add_medicine():

    if request.method == "POST":

        success, message = create_medicine(
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        return redirect(
            url_for("medicine.medicines")
        )
    categories = get_categories()

    return render_template(
        "medicine/add_medicine.html",
        categories=categories
    )
       
# =====================================
# Edit Medicine
# =====================================

@medicine_bp.route("/medicines/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_medicine(id):

    medicine = get_medicine(id)

    if request.method == "POST":

        success, message = update_medicine(
            medicine,
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        return redirect(
            url_for("medicine.medicines")
        )

    categories = get_categories()

    return render_template(
        "medicine/edit_medicine.html",
        medicine=medicine,
        categories=categories
    )
# =====================================
# Delete Medicine
# =====================================

@medicine_bp.route("/medicines/delete/<int:id>", methods=["POST"])
@login_required
def delete_medicine(id):


    medicine = get_medicine(id)

    success, message = delete_medicine_record(
        medicine
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("medicine.medicines")
    )