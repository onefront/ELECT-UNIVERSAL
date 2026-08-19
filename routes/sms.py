from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from flask_login import login_required, current_user

from extensions import db
from models import Voter, SMSLog
from services.sms_service import BMSSMSService

sms_bp = Blueprint(
    "sms",
    __name__,
    url_prefix="/admin/sms"
)


@sms_bp.route("/")
@login_required
def index():

    sms_logs = SMSLog.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(
        SMSLog.created_at.desc()
    ).all()

    return render_template(
        "admin/sms/index.html",
        sms_logs=sms_logs
    )



@sms_bp.route(
    "/delete/<int:sms_id>",
    methods=["POST"]
)
@login_required
def delete_sms(sms_id):

    sms_log = SMSLog.query.filter_by(
        id=sms_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    db.session.delete(sms_log)
    db.session.commit()

    flash(
        "SMS history record deleted successfully.",
        "success"
    )

    return redirect(
        url_for("sms.index")
    )




@sms_bp.route(
    "/compose",
    methods=["GET", "POST"]
)
@login_required
def compose():

    voters = Voter.query.filter_by(
        institution_id=current_user.institution_id,
        status="active"
    ).order_by(
        Voter.id.asc()
    ).all()

    # =========================
    # POST - SEND BULK SMS
    # =========================
    if request.method == "POST":

        recipient_type = request.form.get(
            "recipient_type",
            "all"
        )

        message = request.form.get(
            "message",
            ""
        ).strip()

        # Validate message
        if not message:

            flash(
                "Please enter an SMS message.",
                "warning"
            )

            return render_template(
                "admin/sms/compose.html",
                voters=voters
            )

        # Get recipients
        if recipient_type == "selected":

            selected_ids = request.form.getlist(
                "voter_ids"
            )

            recipients = [
                voter
                for voter in voters
                if str(voter.id) in selected_ids
                and voter.phone
            ]

        else:

            recipients = [
                voter
                for voter in voters
                if voter.phone
            ]

        # Validate recipients
        if not recipients:

            flash(
                "No voters with phone numbers were found.",
                "warning"
            )

            return render_template(
                "admin/sms/compose.html",
                voters=voters
            )

        # Extract phone numbers
        phone_numbers = [
            voter.phone.strip()
            for voter in recipients
            if voter.phone
        ]

        if not phone_numbers:

            flash(
                "No valid phone numbers were found.",
                "warning"
            )

            return render_template(
                "admin/sms/compose.html",
                voters=voters
            )

        # Create SMS log
        sms_log = SMSLog(
            institution_id=current_user.institution_id,
            message=message,
            recipient_count=len(phone_numbers),
            status="pending"
        )

        db.session.add(sms_log)
        db.session.commit()

        # Send through BMS
        service = BMSSMSService()

        result = service.send_sms(
            phone_numbers,
            message
        )

        # Process result
        if result["success"]:

            sms_log.status = "sent"

            db.session.commit()

            flash(
                f"SMS sent successfully to "
                f"{len(phone_numbers)} voter(s).",
                "success"
            )

        else:

            sms_log.status = "failed"

            db.session.commit()

            flash(
                f"SMS sending failed: "
                f"{result.get('message', 'Unknown error')}",
                "danger"
            )

        return redirect(
            url_for("sms.index")
        )

    # =========================
    # GET - SHOW COMPOSE PAGE
    # =========================

    return render_template(
        "admin/sms/compose.html",
        voters=voters
    )



@sms_bp.route("/settings")
@login_required
def settings():

    service = BMSSMSService()

    return render_template(
        "admin/sms/settings.html",
        bms_configured=service.is_configured(),
        bms_enabled=service.enabled,
        sender_id=service.sender_id
    )

@sms_bp.route("/settings/test", methods=["POST"])
@login_required
def test_settings():

    service = BMSSMSService()

    result = service.test_configuration()

    if result["success"]:

        flash(
            "BMS configuration is valid and ready for testing.",
            "success"
        )

    else:

        flash(
            result["message"],
            "danger"
        )

    return redirect(
        url_for("sms.settings")
    )

@sms_bp.route("/settings/test-sms", methods=["POST"])
@login_required
def test_sms():

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    message = request.form.get(
        "message",
        ""
    ).strip()

    service = BMSSMSService()

    result = service.send_test_sms(
        phone,
        message
    )

    if result["success"]:

        flash(
            result["message"],
            "success"
        )

    else:

        flash(
            result["message"],
            "danger"
        )

    return redirect(
        url_for("sms.settings")
    )