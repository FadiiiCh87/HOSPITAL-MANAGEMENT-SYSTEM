import os

from flask import Flask, jsonify
from sqlalchemy import text
from config import Config

from app.extensions import db, migrate, login_manager


def create_app(test_config=None):

    app = Flask(__name__)

    app.config.from_object(Config)
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


    # Flask-Login User Loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Admin, int(user_id))

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

    return app
