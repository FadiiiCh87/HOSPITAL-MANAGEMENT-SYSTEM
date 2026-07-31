from app.extensions import db


class Laboratory(db.Model):

    __tablename__ = "laboratory"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    test_name = db.Column(
        db.String(100),
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    description = db.Column(
        db.Text
    )