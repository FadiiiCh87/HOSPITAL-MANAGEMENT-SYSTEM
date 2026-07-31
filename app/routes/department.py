from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required

from app.services.department_service import (
    get_departments,
    get_department,
    create_department,
    update_department,
    delete_department_record
)

department_bp = Blueprint(
    "department",
    __name__
)

# ======================================================
# Department List
# ======================================================

@department_bp.route("/departments")
@login_required
def departments():

    search = request.args.get(
        "search",
        ""
    ).strip()

    departments = get_departments(
        search
    )

    return render_template(
        "department/departments.html",
        departments=departments,
        search=search
    )

# ======================================================
# Add Department
# ======================================================

@department_bp.route(
    "/departments/add",
    methods=["GET", "POST"]
)
@login_required
def add_department():

    if request.method == "POST":

        success, message = create_department(
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:

            return redirect(
                url_for(
                    "department.departments"
                )
            )

        return redirect(
            url_for(
                "department.add_department"
            )
        )

    return render_template(
        "department/add_department.html"
    )

# ======================================================
# Edit Department
# ======================================================

@department_bp.route(
    "/departments/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_department(id):

    department = get_department(id)

    if request.method == "POST":

        success, message = update_department(
            department,
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:

            return redirect(
                url_for(
                    "department.departments"
                )
            )

        return redirect(
            url_for(
                "department.edit_department",
                id=id
            )
        )

    return render_template(
        "department/edit_department.html",
        department=department
    )

# ======================================================
# Delete Department
# ======================================================

@department_bp.route(
    "/departments/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_department(id):

    department = get_department(id)

    success, message = delete_department_record(
        department
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for(
            "department.departments"
        )
    )