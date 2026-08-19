from extensions import db


class BallotSelection(db.Model):
    __tablename__ = "ballot_selections"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    ballot_id = db.Column(
        db.Integer,
        db.ForeignKey("ballots.id"),
        nullable=False,
        index=True
    )

    position_id = db.Column(
        db.Integer,
        db.ForeignKey("positions.id"),
        nullable=False,
        index=True
    )

    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("candidates.id"),
        nullable=False,
        index=True
    )

    position = db.relationship(
        "Position",
        backref=db.backref(
            "ballot_selections",
            lazy=True
        )
    )

    candidate = db.relationship(
        "Candidate",
        backref=db.backref(
            "ballot_selections",
            lazy=True
        )
    )

    __table_args__ = (
        db.UniqueConstraint(
            "ballot_id",
            "position_id",
            "candidate_id",
            name="uq_ballot_position_candidate"
        ),
    )

    def __repr__(self):
        return (
            f"<BallotSelection "
            f"ballot={self.ballot_id} "
            f"position={self.position_id} "
            f"candidate={self.candidate_id}>"
        )