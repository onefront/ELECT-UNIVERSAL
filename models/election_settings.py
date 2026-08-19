from extensions import db


class ElectionSettings(db.Model):
    __tablename__ = "election_settings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    election_id = db.Column(
        db.Integer,
        db.ForeignKey("elections.id"),
        nullable=False,
        unique=True,
        index=True
    )

    require_voter_verification = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    show_candidate_manifesto = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    show_results_before_close = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    results_published = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )


    allow_abstain = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    election = db.relationship(
        "Election",
        backref=db.backref(
            "settings",
            uselist=False,
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):
        return f"<ElectionSettings election={self.election_id}>"