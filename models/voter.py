from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


class Voter(UserMixin, db.Model):
    __tablename__ = "voters"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    institution_id = db.Column(
        db.Integer,
        db.ForeignKey("institutions.id"),
        nullable=False,
        index=True
    )

    voter_identifier = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    email = db.Column(
        db.String(150),
        nullable=True
    )

    phone = db.Column(
        db.String(50),
        nullable=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=True
    )

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

    institution = db.relationship(
        "Institution",
        backref=db.backref(
            "voters",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False

        return check_password_hash(
            self.password_hash,
            password
        )

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<Voter {self.voter_identifier}>"