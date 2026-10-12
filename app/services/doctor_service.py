from io import BytesIO

from PIL import Image, UnidentifiedImageError
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from sqlalchemy import or_
from app.models.doctor import Doctor
from app.models.department import Department


def get_doctors(search, department, sort, page):

    query = Doctor.query

    if search:
        query = query.filter(
            or_(
                Doctor.full_name.ilike(f"%{search}%"),
                Doctor.email.ilike(f"%{search}%")
            )
        )

    if department:
        query = query.filter(
            Doctor.department_id == int(department)
        )

    if sort == "latest":
        query = query.order_by(Doctor.id.desc())

    elif sort == "oldest":
        query = query.order_by(Doctor.id.asc())

    elif sort == "az":
        query = query.order_by(Doctor.full_name.asc())

    elif sort == "za":
        query = query.order_by(Doctor.full_name.desc())

    elif sort == "exp_high":
        query = query.order_by(Doctor.experience.desc())

    elif sort == "exp_low":
        query = query.order_by(Doctor.experience.asc())

    return query.paginate(
        page=page,
        per_page=10,
        error_out=False
    )


def get_doctor(id):

    return Doctor.query.get_or_404(id)


def get_departments():
    return Department.query.all()


def _read_photo(files):
    photo = files.get("photo")
    if not photo or not photo.filename:
        return None, None, None

    extension = photo.filename.rsplit(".", 1)[-1].lower()
    if extension not in {"png", "jpg", "jpeg"}:
        return False, None, "Only JPG, JPEG and PNG images are allowed."

    image_data = photo.read()
    try:
        with Image.open(BytesIO(image_data)) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        return False, None, "The uploaded file is not a valid image."

    mimetype = "image/png" if extension == "png" else "image/jpeg"
    return image_data, mimetype, None

def create_doctor(form, files):

    full_name = form["full_name"].strip()
    department_id = int(form["department_id"])
    phone = form["phone"]
    email = form["email"].strip().lower()
    gender = form["gender"]
    experience = int(form["experience"])

    existing = Doctor.query.filter_by(email=email).first()

    if existing:
        return False, "Doctor email already exists."

    photo_data, photo_mimetype, error = _read_photo(files)
    if error:
        return False, error

    doctor = Doctor(

        full_name=full_name,
        department_id=department_id,
        phone=phone,
        email=email,
        gender=gender,
        experience=experience,
        photo="" if photo_data else None,
        photo_data=photo_data or None,
        photo_mimetype=photo_mimetype,

    )

    db.session.add(doctor)
    db.session.commit()

    return True, "Doctor Added Successfully!"

def update_doctor(doctor, form, files):
    email = form["email"].strip().lower()

    existing = Doctor.query.filter(
        Doctor.email == email,
        Doctor.id != doctor.id
    ).first()

    if existing:
        return False, "Email already exists."

    doctor.full_name = form["full_name"].strip()
    doctor.department_id = int(form["department_id"])
    doctor.phone = form["phone"].strip()
    doctor.email = email
    doctor.gender = form["gender"]
    doctor.experience = int(form["experience"])

    photo_data, photo_mimetype, error = _read_photo(files)
    if error:
        return False, error
    if photo_data:
        doctor.photo = ""
        doctor.photo_data = photo_data
        doctor.photo_mimetype = photo_mimetype

    db.session.commit()

    return True, "Doctor Updated Successfully!"


def delete_doctor_record(doctor):

    try:

        db.session.delete(doctor)
        db.session.commit()

        return True, "Doctor Deleted Successfully!"

    except IntegrityError:

        db.session.rollback()

        return False, (
            "Cannot delete doctor because related appointments "
            "or other records already exist."
        )
