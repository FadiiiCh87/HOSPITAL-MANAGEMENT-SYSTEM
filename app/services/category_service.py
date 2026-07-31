from sqlalchemy import or_

from app.extensions import db
from app.models.category import Category


def get_categories(page, search="", sort="latest"):

    query = Category.query

    if search:

        query = query.filter(

            or_(

                Category.name.ilike(f"%{search}%"),

                Category.description.ilike(f"%{search}%")

            )

        )

    if sort == "latest":

        query = query.order_by(
            Category.id.desc()
        )

    elif sort == "oldest":

        query = query.order_by(
            Category.id.asc()
        )

    elif sort == "az":

        query = query.order_by(
            Category.name.asc()
        )

    elif sort == "za":

        query = query.order_by(
            Category.name.desc()
        )

    return query.paginate(

        page=page,

        per_page=10,

        error_out=False

    )

def get_category(id):

    return Category.query.get_or_404(id)


def create_category(form):

    name = form["name"].strip()

    description = form["description"].strip()

    existing = Category.query.filter_by(
        name=name
    ).first()

    if existing:

        return (
            False,
            "Category already exists."
        )

    category = Category(

        name=name,

        description=description

    )

    db.session.add(category)

    db.session.commit()

    return (
        True,
        "Category Added Successfully!"
    )


def update_category(category, form):

    name = form["name"].strip()

    existing = Category.query.filter(

        Category.name == name,

        Category.id != category.id

    ).first()

    if existing:

        return (
            False,
            "Category already exists."
        )

    category.name = name

    category.description = form["description"]

    db.session.commit()

    return (
        True,
        "Category Updated Successfully!"
    )


def delete_category_record(category):

    db.session.delete(category)

    db.session.commit()

    return (
        True,
        "Category Deleted Successfully!"
    )