from app.services.dashboard_service import get_dashboard_data
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models.admin import Admin


auth_bp = Blueprint("auth", __name__)


# ==========================
# Login
# ==========================
@auth_bp.route("/staff/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated and current_user.role != "Patient":
        return redirect(url_for("portal.patient_dashboard" if current_user.role == "Patient" else "portal.doctor_dashboard" if current_user.role == "Doctor" else "auth.dashboard"))

    if request.method == "POST":

        from app.portal import throttle
        throttle("staff-login")
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        admin = Admin.query.filter_by(email=email).first()

        if admin and check_password_hash(admin.password, password):

            session.pop("pending_booking", None)
            login_user(admin)

            flash("Login Successful", "success")

            return redirect(url_for("portal.doctor_dashboard" if admin.role == "Doctor" else "auth.dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")


# ==========================
# Dashboard
# ==========================
@auth_bp.route("/dashboard")
@login_required
def dashboard():

    dashboard_data = get_dashboard_data()

    
    return render_template(
        "dashboard.html",
        admin=current_user,
        **dashboard_data
    )

# ==========================
# Logout
# ==========================
@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged Out Successfully", "success")

    return redirect(url_for("auth.login"))