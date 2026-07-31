from app.extensions import db
from app.models.laboratory import Laboratory


def get_all_tests(search=""):

    query = Laboratory.query

    if search:

        query = query.filter(
            Laboratory.test_name.ilike(f"%{search}%")
        )

    return query.order_by(
        Laboratory.id.desc()
    ).all()


def get_test(id):

    return Laboratory.query.get_or_404(id)


def create_test(form):

    test = Laboratory(

        test_name=form["test_name"],

        category=form["category"],

        price=float(form["price"]),

        description=form["description"]

    )

    db.session.add(test)
    db.session.commit()
    return True, "Laboratory test added successfully."


def update_test(test, form):

    test.test_name = form["test_name"]

    test.category = form["category"]

    test.price = float(form["price"])

    test.description = form["description"]

    db.session.commit()
    return True, "Laboratory test updated successfully."


def delete_test_record(test):

    db.session.delete(test)

    db.session.commit()
    return True, "Laboratory test deleted successfully."