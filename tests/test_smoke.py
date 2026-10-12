import io
import os
import tempfile
import unittest

from PIL import Image
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.department import Department
from app.models.doctor import Doctor


class HospitalSmokeTests(unittest.TestCase):
    def setUp(self):
        self.database_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.database_file.close()
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.database_file.name}",
                "SQLALCHEMY_ENGINE_OPTIONS": {},
                "SESSION_COOKIE_SECURE": False,
            }
        )
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            db.session.add(
                Admin(
                    full_name="Test Admin",
                    email="admin@example.com",
                    password=generate_password_hash("safe-test-password"),
                    role="Admin",
                )
            )
            db.session.add(Department(name="Cardiology"))
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        os.unlink(self.database_file.name)

    def login(self):
        response = self.client.post(
            "/",
            data={"email": "admin@example.com", "password": "safe-test-password"},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Login Successful", response.data)

    def test_health_login_and_core_pages(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.login()

        pages = [
            "/dashboard", "/doctors", "/departments", "/patients",
            "/appointments", "/categories", "/medicines", "/laboratory",
            "/lab-requests", "/prescriptions", "/billing", "/reports/revenue",
            "/reports/appointments", "/users",
        ]
        for page in pages:
            with self.subTest(page=page):
                self.assertEqual(self.client.get(page).status_code, 200)

    def test_doctor_photo_persists_in_database(self):
        self.login()
        image = io.BytesIO()
        Image.new("RGB", (8, 8), color="navy").save(image, format="PNG")
        image.seek(0)

        response = self.client.post(
            "/doctors/add",
            data={
                "full_name": "Dr Test",
                "department_id": "1",
                "phone": "0500000000",
                "email": "doctor@example.com",
                "gender": "Male",
                "experience": "5",
                "photo": (image, "doctor.png"),
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            doctor = Doctor.query.filter_by(email="doctor@example.com").one()
            doctor_id = doctor.id
            self.assertTrue(doctor.photo_data)
            self.assertEqual(doctor.photo_mimetype, "image/png")

        photo_response = self.client.get(f"/doctors/{doctor_id}/photo")
        self.assertEqual(photo_response.status_code, 200)
        self.assertEqual(photo_response.mimetype, "image/png")


if __name__ == "__main__":
    unittest.main()
