from datetime import datetime

from extensions import db


class Candidate(db.Model):
    __tablename__ = "candidates"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    election_id = db.Column(
        db.Integer,
        db.ForeignKey("elections.id"),
        nullable=False,
        index=True
    )

    position_id = db.Column(
        db.Integer,
        db.ForeignKey("positions.id"),
        nullable=False,
        index=True
    )

    name = db.Column(
        db.String(150),
        nullable=False
    )

    photo = db.Column(
        db.String(255),
        nullable=True
    )

    manifesto = db.Column(
        db.Text,
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

    election = db.relationship(
        "Election",
        backref=db.backref(
            "candidates",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    position = db.relationship(
        "Position",
        backref=db.backref(
            "candidates",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):
        return f"<Candidate {self.name}>"