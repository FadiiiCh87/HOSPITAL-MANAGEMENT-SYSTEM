from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.department import Department
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():

    # Create Default Admin
    if not Admin.query.filter_by(email="admin@hospital.com").first():

        admin = Admin(
            full_name="System Administrator",
            email="admin@hospital.com",
            password=generate_password_hash("admin123")
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