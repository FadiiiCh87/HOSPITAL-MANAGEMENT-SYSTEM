from app.extensions import db
from datetime import datetime
from app.models.bill import Bill
from app.models.patient import Patient


from sqlalchemy import or_


def get_all_bills(search, status, sort, page):

    query = Bill.query.join(Patient)

    # -------------------------
    # Search
    # -------------------------

    if search:

        query = query.filter(

            or_(

                Patient.full_name.ilike(f"%{search}%"),

                Bill.invoice_no.ilike(f"%{search}%")

            )

        )

    # -------------------------
    # Payment Filter
    # -------------------------

    if status:

        query = query.filter(
            Bill.payment_status == status
        )

    # -------------------------
    # Sorting
    # -------------------------

    if sort == "latest":

        query = query.order_by(
            Bill.id.desc()
        )

    elif sort == "oldest":

        query = query.order_by(
            Bill.id.asc()
        )

    elif sort == "highest":

        query = query.order_by(
            Bill.total_amount.desc()
        )

    elif sort == "lowest":

        query = query.order_by(
            Bill.total_amount.asc()
        )

    return query.paginate(

        page=page,

        per_page=10,

        error_out=False

    )


def get_patients():

    return Patient.query.order_by(
        Patient.full_name
    ).all()


def get_bill(id):

    return Bill.query.get_or_404(id)


def create_bill(form):

    consultation_fee = float(
        form["consultation_fee"]
    )

    medicine_charge = float(
        form["medicine_charge"]
    )

    other_charge = float(
        form["other_charge"]
    )

    total_amount = (
        consultation_fee +
        medicine_charge +
        other_charge
    )

    last_bill = Bill.query.order_by(
        Bill.id.desc()
    ).first()

    if last_bill:

        next_id = last_bill.id + 1

    else:

        next_id = 1

    invoice_no = f"INV-{datetime.now().year}{next_id:04d}"

    bill = Bill(
        invoice_no=invoice_no,

        patient_id=form["patient_id"],

        consultation_fee=consultation_fee,

        medicine_charge=medicine_charge,

        other_charge=other_charge,

        total_amount=total_amount

    )

    db.session.add(bill)

    db.session.commit()

    return True, "Bill Created Successfully!"


def update_bill(bill, form):

    bill.patient_id = form["patient_id"]

    bill.consultation_fee = float(
        form["consultation_fee"]
    )

    bill.medicine_charge = float(
        form["medicine_charge"]
    )

    bill.other_charge = float(
        form["other_charge"]
    )

    bill.payment_status = form[
        "payment_status"
    ]

    bill.total_amount = (

        bill.consultation_fee +

        bill.medicine_charge +

        bill.other_charge

    )

    db.session.commit()
    return True, "Bill Updated Successfully!"


def delete_bill_record(bill):

    db.session.delete(bill)

    db.session.commit()

    return True, "Bill Deleted Successfully!"