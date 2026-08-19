from datetime import datetime

from extensions import db


class Institution(db.Model):
    __tablename__ = "institutions"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)

    logo = db.Column(db.String(255), nullable=True)

    primary_color = db.Column(
        db.String(20),
        nullable=False,
        default="#0d6efd"
    )

    secondary_color = db.Column(
        db.String(20),
        nullable=False,
        default="#ffffff"
    )

    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="active"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Institution {self.name}>"