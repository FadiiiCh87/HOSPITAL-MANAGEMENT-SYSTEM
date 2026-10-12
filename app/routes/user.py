from sqlalchemy import or_
from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from app.utils.permissions import admin_required
from werkzeug.security import generate_password_hash
from flask import render_template
from app.models.admin import Admin
from app.extensions import db
from flask import Blueprint
from flask_login import login_required, current_user

user_bp = Blueprint(
    "user",
    __name__
)

@user_bp.route("/users")
@login_required
@admin_required
def users():

    search = request.args.get("search", "")

    users_query = Admin.query

    if search:

        users_query = users_query.filter(
            or_(
                Admin.full_name.ilike(f"%{search}%"),
                Admin.email.ilike(f"%{search}%")
            )
        )

    page = request.args.get(
    "page",
    1,
    type=int
    )

    users = (
        users_query
        .order_by(Admin.id.desc())
        .paginate(
            page=page,
            per_page=10
        )
    )

    return render_template(
        "users/users.html",
        users=users,
        search=search
    )
@user_bp.route("/users/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_user():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        existing = Admin.query.filter_by(
            email=email
        ).first()

        if existing:

            flash(
                "Email already exists.",
                "danger"
            )

            return redirect(
                url_for("user.add_user")
            )

        user = Admin(

            full_name=full_name,

            email=email,

            password=generate_password_hash(password),

            role=role

        )

        db.session.add(user)

        db.session.commit()

        flash(
            "User added successfully.",
            "success"
        )

        return redirect(
            url_for("user.users")
        )

    return render_template(
        "users/add_user.html"
    )
@user_bp.route("/users/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(id):

    user = Admin.query.get_or_404(id)

    if request.method == "POST":

        user.full_name = request.form["full_name"]
        user.email = request.form["email"]
        user.role = request.form["role"]

        password = request.form["password"]

        if password.strip():

            user.password = generate_password_hash(password)

        db.session.commit()

        flash(
            "User updated successfully.",
            "success"
        )

        return redirect(
            url_for("user.users")
        )

    return render_template(
        "users/edit_user.html",
        user=user
    )
@user_bp.route("/users/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def delete_user(id):

    user = Admin.query.get_or_404(id)

    if user.id == current_user.id:

        flash(
            "You cannot delete your own account.",
            "danger"
        )

        return redirect(
            url_for("user.users")
        )

    db.session.delete(user)

    db.session.commit()

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("user.users")
    )
