from app.extensions import db


class Medicine(db.Model):
    __tablename__ = "medicines"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    company = db.Column(db.String(150), nullable=False)

    price = db.Column(db.Float, nullable=False)

    quantity = db.Column(db.Integer, nullable=False)

    expiry_date = db.Column(db.Date, nullable=False)

    category_id = db.Column(
    db.Integer,
    db.ForeignKey("categories.id")
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )