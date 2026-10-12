import os

from flask import Flask, jsonify, request, abort, redirect, url_for
from sqlalchemy import text
from config import Config

from app.extensions import db, migrate, login_manager


def create_app(test_config=None):

    app = Flask(__name__)

    app.config.from_object(Config)
    if os.getenv("RENDER") == "true":
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Import Models
    from app.models.admin import Admin
    from app.models.department import Department
    from app.models.doctor import Doctor
    from app.models.patient import Patient
    from app.models.appointment import Appointment
    from app.routes.appointment import appointment_bp
    from app.routes.medicine import medicine_bp
    from app.models.bill import Bill
    from app.models.laboratory import Laboratory
    from app.routes.laboratory import laboratory_bp
    from app.routes.billing import billing_bp
    from app.routes.report import report_bp
    from app.routes.user import user_bp
    from app.models.lab_request import LabRequest
    from app.routes.lab_request import lab_request_bp
    from app.models.prescription import Prescription
    from app.routes.prescription import prescription_bp
    from app.routes.department import department_bp
    from app.routes.category import category_bp
    from app.models.category import Category
    from app.models.medicine import Medicine

    app.register_blueprint(department_bp)
    app.register_blueprint(category_bp)


    from app.models.portal import PatientAccount
    from app.portal import portal, throttle
    from flask_login import current_user
    from flask_wtf.csrf import CSRFProtect
    CSRFProtect(app)
    app.register_blueprint(portal)

    @app.before_request
    def enforce_access():
        if request.endpoint and request.endpoint.startswith(("portal.", "static")) or request.endpoint == "health":
            return
        if current_user.is_authenticated:
            if current_user.role == "Patient":
                abort(403)
            if current_user.role == "Doctor" and request.endpoint not in {"auth.login", "auth.logout"}:
                abort(403)
            if current_user.role == "Receptionist" and request.blueprint not in {"auth","patient","appointment","billing","lab_request"}:
                abort(403)
            if current_user.role == "Pharmacist" and request.blueprint not in {"auth","medicine","category","laboratory"}:
                abort(403)
            if current_user.role not in {"Admin","Doctor","Receptionist","Pharmacist"}:
                abort(403)
            if request.blueprint not in {"auth"}:
                from app.portal import audit
                audit("staff_" + request.method.lower(), request.path)
                db.session.commit()

    @app.after_request
    def private_headers(response):
        if current_user.is_authenticated or request.path.startswith(("/patient", "/doctor", "/admin", "/staff")):
            response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response

    # Flask-Login User Loader
    @login_manager.user_loader
    def load_user(user_id):
        try:
            if user_id.startswith("patient:"):
                parts = user_id.split(":")
                account = db.session.get(PatientAccount, int(parts[1]))
                return account if account and len(parts)==3 and account.token_version==int(parts[2]) else None
            return db.session.get(Admin, int(user_id))
        except (ValueError, TypeError):
            return None

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.doctor import doctor_bp
    from app.routes.patient import patient_bp
    from app.models.medicine import Medicine
    app.register_blueprint(auth_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(medicine_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(laboratory_bp)
    app.register_blueprint(lab_request_bp)
    app.register_blueprint(prescription_bp)

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
        except Exception:
            app.logger.exception("Database health check failed")
            return jsonify(status="unhealthy"), 503
        return jsonify(status="ok"), 200

    from sqlalchemy.exc import IntegrityError
    @app.errorhandler(IntegrityError)
    def conflict(error):
        db.session.rollback()
        return "This change conflicts with an existing record or appointment. Go back and choose another slot.", 409

    return app
