from app.extensions import db


class Bill(db.Model):
    __tablename__ = "bills"

    id = db.Column(db.Integer, primary_key=True)

    invoice_no = db.Column(
    db.String(20),
    unique=True,
    nullable=False
)

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patients.id"),
        nullable=False
    )

    consultation_fee = db.Column(
        db.Float,
        default=0
    )

    medicine_charge = db.Column(
        db.Float,
        default=0
    )

    other_charge = db.Column(
        db.Float,
        default=0
    )

    total_amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_status = db.Column(
        db.String(30),
        default="Unpaid"
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )
    patient = db.relationship(
        "Patient",
        back_populates="bills"
    )