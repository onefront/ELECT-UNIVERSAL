from datetime import datetime

from extensions import db


class SMSLog(db.Model):

    __tablename__ = "sms_logs"

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

    message = db.Column(
        db.Text,
        nullable=False
    )

    recipient_count = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    sent_at = db.Column(
        db.DateTime,
        nullable=True
    )