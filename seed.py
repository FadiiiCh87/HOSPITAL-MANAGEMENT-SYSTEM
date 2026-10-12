import os
import re

from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.department import Department
from werkzeug.security import generate_password_hash
from sqlalchemy import text

app = create_app()

with app.app_context():
    schema = os.getenv("DB_SCHEMA")
    if schema:
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", schema):
            raise RuntimeError("DB_SCHEMA contains unsupported characters")
        db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
        db.session.commit()

    db.create_all()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@hospital.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError("ADMIN_PASSWORD must be set before database initialization")

    # Create Default Admin
    if not Admin.query.filter_by(email=admin_email).first():

        admin = Admin(
            full_name="System Administrator",
            email=admin_email,
            password=generate_password_hash(admin_password),
            role="Admin",
        )

        db.session.add(admin)

    # Default Departments
    departments = [
        "Cardiology",
        "Neurology",
        "Orthopedics",
        "ENT",
        "Emergency",
        "Radiology",
        "Laboratory",
        "Pharmacy"
    ]

    for dept in departments:

        if not Department.query.filter_by(name=dept).first():

            db.session.add(
                Department(name=dept)
            )

    db.session.commit()

    print("Database Seeded Successfully!")
