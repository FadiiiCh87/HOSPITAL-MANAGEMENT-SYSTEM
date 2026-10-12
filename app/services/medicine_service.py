from datetime import date
from sqlalchemy import or_
from app.models.category import Category
from app.extensions import db
from app.models.medicine import Medicine


def get_medicines(search, sort, filter_by="", page=1):

    query = Medicine.query

    if search:

        query = query.filter(

            or_(

                Medicine.name.ilike(f"%{search}%"),
                Medicine.company.ilike(f"%{search}%")

            )

        )

    # Filters
    if filter_by == "expired":

        query = query.filter(
            Medicine.expiry_date < date.today()
        )

    elif filter_by == "low":

        query = query.filter(Medicine.quantity <= 5, Medicine.quantity > 0)

    elif filter_by == "out":

        query = query.filter(Medicine.quantity == 0)

    

    # Sorting

    if sort == "latest":

        query = query.order_by(Medicine.id.desc())

    elif sort == "oldest":

        query = query.order_by(Medicine.id.asc())

    elif sort == "az":

        query = query.order_by(Medicine.name.asc())

    elif sort == "za":

        query = query.order_by(Medicine.name.desc())

    elif sort == "price_high":

        query = query.order_by(Medicine.price.desc())

    elif sort == "price_low":

        query = query.order_by(Medicine.price.asc())

    return query.paginate(

        page=page,

        per_page=10,

        error_out=False

    )

def get_medicine(id):

    return Medicine.query.get_or_404(id)




def create_medicine(form):

    medicine = Medicine(
        name=form["name"],
        company=form["company"],
        price=float(form["price"]),
        quantity=int(form["quantity"]),
        expiry_date=form["expiry_date"],
        category_id=form["category_id"]
    )

    db.session.add(medicine)
    db.session.commit()

    return True, "Medicine Added Successfully!"


def update_medicine(medicine, form):

    medicine.name = form["name"]
    medicine.company = form["company"]
    medicine.category_id = form["category_id"]
    medicine.price = float(form["price"])
    medicine.quantity = int(form["quantity"])
    medicine.expiry_date = form["expiry_date"]

    db.session.commit()
    return True, "Medicine Updated Successfully!"


def delete_medicine_record(medicine):

    db.session.delete(medicine)
    db.session.commit()
    return True, "Medicine Deleted Successfully!"


def get_today():

    return date.today()

def get_categories():

    return Category.query.order_by(
        Category.name.asc()
    ).all()



from sqlalchemy import func

def get_medicine_statistics():

    total = Medicine.query.count()

    in_stock = Medicine.query.filter(
        Medicine.quantity > 5
    ).count()

    low_stock = Medicine.query.filter(
        Medicine.quantity.between(1, 5)
    ).count()

    out_of_stock = Medicine.query.filter(
        Medicine.quantity == 0
    ).count()

    expired = Medicine.query.filter(
        Medicine.expiry_date < get_today()
    ).count()

    return {

        "total": total,

        "in_stock": in_stock,

        "low_stock": low_stock,

        "out_of_stock": out_of_stock,

        "expired": expired

    }
