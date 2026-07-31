import os
import uuid
from flask import current_app, flash, redirect, url_for
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

def create_doctor(form, files):

    full_name = form["full_name"]
    department_id = int(form["department_id"])
    phone = form["phone"]
    email = form["email"]
    gender = form["gender"]
    experience = int(form["experience"])

    existing = Doctor.query.filter_by(email=email).first()

    if existing:
        return False, "Doctor email already exists."

    photo_name = ""

    photo = files.get("photo")

    if photo and photo.filename != "":

        extension = photo.filename.rsplit(".", 1)[1].lower()

        if extension not in {"png", "jpg", "jpeg"}:
            return False, "Only JPG, JPEG and PNG images are allowed."

        filename = f"{uuid.uuid4()}.{extension}"

        photo.save(
            os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        photo_name = filename

    doctor = Doctor(

        full_name=full_name,
        department_id=department_id,
        phone=phone,
        email=email,
        gender=gender,
        experience=experience,
        photo=photo_name

    )

    db.session.add(doctor)
    db.session.commit()

    return True, "Doctor Added Successfully!"

def update_doctor(doctor, form, files):

    doctor.full_name = form["full_name"]
    doctor.department_id = int(form["department_id"])
    doctor.phone = form["phone"]
    doctor.email = form["email"]
    doctor.gender = form["gender"]
    doctor.experience = int(form["experience"])

    existing = Doctor.query.filter(
        Doctor.email == doctor.email,
        Doctor.id != doctor.id
    ).first()

    if existing:
        return False, "Email already exists."

    photo = files.get("photo")

    if photo and photo.filename != "":

        extension = photo.filename.rsplit(".", 1)[1].lower()

        if extension not in {"png", "jpg", "jpeg"}:
            return False, "Only JPG, JPEG and PNG images are allowed."

        if doctor.photo:

            old_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                doctor.photo
            )

            if os.path.exists(old_path):
                os.remove(old_path)

        filename = f"{uuid.uuid4()}.{extension}"

        photo.save(
            os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                filename
            )
        )

        doctor.photo = filename

    db.session.commit()

    return True, "Doctor Updated Successfully!"


def delete_doctor_record(doctor):

    try:

        if doctor.photo:

            image_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                doctor.photo
            )

            if os.path.exists(image_path):
                os.remove(image_path)

        db.session.delete(doctor)
        db.session.commit()

        return True, "Doctor Deleted Successfully!"

    except IntegrityError:

        db.session.rollback()

        return False, (
            "Cannot delete doctor because related appointments "
            "or other records already exist."
        )