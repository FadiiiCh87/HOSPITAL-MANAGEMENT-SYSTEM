from app.extensions import db

class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    description = db.Column(
        db.Text
    )

    medicines = db.relationship(
        "Medicine",
        backref="category",
        lazy=True
    )