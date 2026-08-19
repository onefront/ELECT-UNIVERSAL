from extensions import db


class Position(db.Model):
    __tablename__ = "positions"

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

    name = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    display_order = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    max_selections = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    election = db.relationship(
        "Election",
        backref=db.backref(
            "positions",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    def __repr__(self):
        return f"<Position {self.name}>"