from datetime import datetime

from extensions import db


class ElectionVoter(db.Model):
    __tablename__ = "election_voters"

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

    voter_id = db.Column(
        db.Integer,
        db.ForeignKey("voters.id"),
        nullable=False,
        index=True
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="eligible"
    )

    has_voted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    voted_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    election = db.relationship(
        "Election",
        backref=db.backref(
            "eligible_voters",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    voter = db.relationship(
        "Voter",
        backref=db.backref(
            "election_entries",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "election_id",
            "voter_id",
            name="uq_election_voter"
        ),
    )

    def __repr__(self):
        return (
            f"<ElectionVoter "
            f"election={self.election_id} "
            f"voter={self.voter_id}>"
        )