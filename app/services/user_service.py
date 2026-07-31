from werkzeug.security import generate_password_hash
from sqlalchemy import or_

from app.extensions import db
from app.models.admin import Admin


def get_users(search, page):

    query = Admin.query

    if search:

        query = query.filter(

            or_(

                Admin.full_name.ilike(f"%{search}%"),
                Admin.email.ilike(f"%{search}%")

            )

        )

    return query.order_by(
        Admin.id.desc()
    ).paginate(
        page=page,
        per_page=10
    )


def get_user(id):

    return Admin.query.get_or_404(id)


def create_user(form):

    user = Admin(

        full_name=form["full_name"],
        email=form["email"],
        password=generate_password_hash(form["password"]),
        role=form["role"]

    )

    db.session.add(user)
    db.session.commit()


def update_user(user, form):

    user.full_name = form["full_name"]
    user.email = form["email"]
    user.role = form["role"]

    password = form["password"]

    if password.strip():

        user.password = generate_password_hash(password)

    db.session.commit()


def delete_user_record(user):

    db.session.delete(user)
    db.session.commit()


def email_exists(email):

    return Admin.query.filter_by(
        email=email
    ).first()