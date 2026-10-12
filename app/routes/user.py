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
from app.models.doctor import Doctor
from app.models.portal import DoctorAccount
from sqlalchemy.exc import IntegrityError
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
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]
        if role not in {"Admin", "Receptionist", "Pharmacist", "Doctor", "Lab Staff", "Cashier"}:
            flash("Create doctor access through V2 schedules & access.", "warning")
            return redirect(url_for("user.users"))

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

        if not sync_doctor(user, role):
            db.session.rollback()
            return redirect(url_for("user.add_user"))
        db.session.commit()

        flash(
            "User added successfully.",
            "success"
        )

        return redirect(
            url_for("user.users")
        )

    return render_template(
        "users/add_user.html", doctors=Doctor.query.order_by(Doctor.full_name).all()
    )
@user_bp.route("/users/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(id):

    user = Admin.query.get_or_404(id)

    if request.method == "POST":

        user.full_name = request.form["full_name"]
        user.email = request.form["email"].strip().lower().strip().lower()
        if request.form["role"] not in {"Admin", "Receptionist", "Pharmacist", "Doctor", "Lab Staff", "Cashier"}:
            flash("Doctor roles are managed through V2 linked accounts.", "warning")
            return redirect(url_for("user.users"))
        user.role = request.form["role"]

        password = request.form["password"]

        if password.strip():

            user.password = generate_password_hash(password)

        if not sync_doctor(user, user.role):
            db.session.rollback()
            return redirect(url_for("user.edit_user", id=id))
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
        user=user, doctors=Doctor.query.order_by(Doctor.full_name).all(), doctor_link=DoctorAccount.query.filter_by(admin_id=user.id).first()
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

    DoctorAccount.query.filter_by(admin_id=user.id).delete()
    db.session.delete(user)

    db.session.commit()

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("user.users")
    )


def sync_doctor(user, role):
    link = DoctorAccount.query.filter_by(admin_id=user.id).first() if user.id else None
    if role != "Doctor":
        if link: db.session.delete(link)
        return True
    did = request.form.get("doctor_id", type=int)
    doctor = db.session.get(Doctor, did) if did else None
    other = DoctorAccount.query.filter_by(doctor_id=did).first() if did else None
    if not doctor or (other and other.admin_id != user.id):
        flash("Select a doctor without another linked staff account.", "danger")
        return False
    db.session.flush()
    if link: link.doctor_id = did
    else: db.session.add(DoctorAccount(admin_id=user.id, doctor_id=did))
    return True
