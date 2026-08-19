from datetime import datetime

from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

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

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    action = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text,
        nullable=True
    )

    entity_type = db.Column(
        db.String(50),
        nullable=True
    )

    entity_id = db.Column(
        db.Integer,
        nullable=True
    )

    ip_address = db.Column(
        db.String(45),
        nullable=True
    )

    user_agent = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    institution = db.relationship(
        "Institution",
        backref=db.backref(
            "audit_logs",
            lazy=True
        )
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "audit_logs",
            lazy=True
        )
    )

    def __repr__(self):
        return (
            f"<AuditLog "
            f"{self.action} "
            f"user={self.user_id}>"
        )