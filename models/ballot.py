from datetime import datetime
import uuid

from extensions import db


class Ballot(db.Model):
    __tablename__ = "ballots"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    ballot_uuid = db.Column(
        db.String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    election_id = db.Column(
        db.Integer,
        db.ForeignKey("elections.id"),
        nullable=False,
        index=True
    )

    cast_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    election = db.relationship(
        "Election",
        backref=db.backref(
            "ballots",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    selections = db.relationship(
        "BallotSelection",
        backref="ballot",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Ballot {self.ballot_uuid}>"