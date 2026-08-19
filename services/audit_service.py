from flask import request
from flask_login import current_user

from extensions import db
from models import AuditLog


def log_activity(
    action,
    description=None,
    entity_type=None,
    entity_id=None,
    voter=None
):
    """
    Record an administrative or voter activity.
    """

    # Voter activity
    if voter is not None:

        log = AuditLog(
            institution_id=voter.institution_id,
            user_id=None,
            action=action,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get("User-Agent")
        )

        db.session.add(log)
        db.session.commit()

        return

    # Administrator activity
    if not current_user.is_authenticated:
        return

    log = AuditLog(
        institution_id=current_user.institution_id,
        user_id=current_user.id,
        action=action,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )

    db.session.add(log)
    db.session.commit()