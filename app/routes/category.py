from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import login_required

from app.services.category_service import (
    get_categories,
    get_category,
    create_category,
    update_category,
    delete_category_record
)


category_bp = Blueprint(
    "category",
    __name__
)

# ==========================================
# Categories List
# ==========================================

@category_bp.route("/categories")
@login_required
def categories():

    page = request.args.get(
        "page",
        1,
        type=int
    )

    search = request.args.get(
        "search",
        ""
    ).strip()

    sort = request.args.get(
        "sort",
        "latest"
    )

    categories = get_categories(
        page,
        search,
        sort
    )

    return render_template(
        "category/categories.html",
        categories=categories,
        search=search,
        sort=sort
    )


# ==========================================
# Add Category
# ==========================================

@category_bp.route(
    "/categories/add",
    methods=["GET", "POST"]
)
@login_required
def add_category():

    if request.method == "POST":

        success, message = create_category(
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:

            return redirect(
                url_for("category.categories")
            )

    return render_template(
        "category/add_category.html"
    )

# ==========================================
# Edit Category
# ==========================================

@category_bp.route(
    "/categories/edit/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def edit_category(id):

    category = get_category(id)

    if request.method == "POST":

        success, message = update_category(
            category,
            request.form
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:

            return redirect(
                url_for("category.categories")
            )

    return render_template(
        "category/edit_category.html",
        category=category
    )

# ==========================================
# Delete Category
# ==========================================

@category_bp.route(
    "/categories/delete/<int:id>",
    methods=["POST"]
)
@login_required
def delete_category(id):

    category = get_category(id)

    success, message = delete_category_record(
        category
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("category.categories")
    )