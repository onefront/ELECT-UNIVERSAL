from datetime import datetime

from extensions import db


class Election(db.Model):
    __tablename__ = "elections"

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

    name = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    start_date = db.Column(
        db.DateTime,
        nullable=False
    )

    end_date = db.Column(
        db.DateTime,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="draft"
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
            "elections",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<Election {self.name}>"