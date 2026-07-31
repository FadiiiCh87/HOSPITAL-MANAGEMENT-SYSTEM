from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from flask_login import login_required
from app.services.laboratory_service import (
    get_all_tests,
    get_test,
    create_test,
    update_test,
    delete_test_record
)

laboratory_bp = Blueprint(
    "laboratory",
    __name__
)


@laboratory_bp.route("/laboratory")
@login_required
def laboratory():

    search = request.args.get("search", "")

    tests = get_all_tests(search)

    return render_template(
        "laboratory/laboratory.html",
        tests=tests,
        search=search
    )


@laboratory_bp.route(
    "/laboratory/add",
    methods=["GET", "POST"]
)
@login_required
def add_test():

    if request.method == "POST":

        success, message = create_test(
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        return redirect(
            url_for("laboratory.laboratory")
        )

    return render_template(
        "laboratory/add_test.html"
    )


@laboratory_bp.route(
    "/laboratory/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_test(id):

    test = get_test(id)

    if request.method == "POST":

        success, message = update_test(
            test,
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        return redirect(
            url_for("laboratory.laboratory")
        )

    return render_template(
        "laboratory/edit_test.html",
        test=test
    )
@laboratory_bp.route(
    "/laboratory/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_test(id):

    test = get_test(id)

    success, message = delete_test_record(
        test
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("laboratory.laboratory")
    )

