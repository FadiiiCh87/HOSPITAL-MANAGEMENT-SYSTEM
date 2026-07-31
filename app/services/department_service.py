from sqlalchemy import or_

from app.extensions import db
from app.models.department import Department


def get_departments(search=""):

    query = Department.query

    if search:

        query = query.filter(

            Department.name.ilike(f"%{search}%")

        )

    return query.order_by(
        Department.id.desc()
    ).all()


def get_department(id):

    return Department.query.get_or_404(id)


def create_department(form):

    existing = Department.query.filter_by(
        name=form["name"]
    ).first()

    if existing:

        return False, "Department already exists."

    department = Department(

        name=form["name"]

    )

    db.session.add(department)

    db.session.commit()

    return True, "Department Added Successfully!"


def update_department(department, form):

    existing = Department.query.filter(

        Department.name == form["name"],

        Department.id != department.id

    ).first()

    if existing:

        return False, "Department already exists."

    department.name = form["name"]

    db.session.commit()

    return True, "Department Updated Successfully!"


def delete_department_record(department):

    db.session.delete(department)

    db.session.commit()

    return True, "Department Deleted Successfully!"