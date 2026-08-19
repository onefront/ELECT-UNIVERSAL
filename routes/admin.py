import os
from werkzeug.utils import secure_filename

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    current_app,
)
from models import (
    Election,
    Voter,
    ElectionVoter,
    Candidate,
    Ballot,
    BallotSelection,
    Institution,
    User,
)


from flask_login import login_required, current_user
from extensions import db



admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


@admin_bp.route("/dashboard")
@login_required
def dashboard():

    institution_id = current_user.institution_id

    # Institution-specific elections
    elections = Election.query.filter_by(
        institution_id=institution_id
    ).all()




    # Institution-specific voters
    voters = Voter.query.filter_by(
        institution_id=institution_id
    ).all()

    # ---------------------------------------------------------
    # VOTER PARTICIPATION
    # ---------------------------------------------------------

    voted_voter_ids = (
        db.session.query(ElectionVoter.voter_id)
        .join(
            Election,
            ElectionVoter.election_id == Election.id
        )
        .filter(
            Election.institution_id == institution_id,
            ElectionVoter.has_voted.is_(True)
        )
        .distinct()
        .all()
    )

    voters_who_voted = len(voted_voter_ids)

    voters_yet_to_vote = max(
        len(voters) - voters_who_voted,
        0
    )

    voter_turnout = (
        (voters_who_voted / len(voters)) * 100
        if voters
        else 0
    )

    # Institution-specific candidates
    election_ids = [election.id for election in elections]

    candidates = []

    if election_ids:
        from models import Candidate

        candidates = Candidate.query.filter(
            Candidate.election_id.in_(election_ids)
        ).all()

    # Institution-specific ballots
    ballots = []

    if election_ids:
        ballots = Ballot.query.filter(
            Ballot.election_id.in_(election_ids)
        ).all()

    # Active elections
    active_elections = [
        election
        for election in elections
        if election.status == "active"
    ]



    # ---------------------------------------------------------
    # TOP POSITIONS - ACTUAL VOTE DISTRIBUTION
    # ---------------------------------------------------------

    position_vote_counts = {}

    if election_ids:

        selections = BallotSelection.query.join(
            Ballot,
            BallotSelection.ballot_id == Ballot.id
        ).filter(
            Ballot.election_id.in_(election_ids)
        ).all()

        for selection in selections:

            if selection.position:

                position_name = selection.position.name

                position_vote_counts[position_name] = (
                    position_vote_counts.get(position_name, 0) + 1
                )

    total_position_votes = sum(
        position_vote_counts.values()
    )

    top_positions = []

    if total_position_votes:

        sorted_positions = sorted(
            position_vote_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )

        colors = [
            "#0d6efd",
            "#20c997",
            "#f59e0b",
            "#6f42c1",
            "#64748b",
        ]

        for index, (name, votes) in enumerate(
            sorted_positions[:5]
        ):

            percentage = round(
                (votes / total_position_votes) * 100,
                1
            )

            top_positions.append({
                "name": name,
                "votes": votes,
                "percentage": percentage,
                "color": colors[
                    index % len(colors)
                ],
            })

        # Group remaining positions as Others
        if len(sorted_positions) > 5:

            others_votes = sum(
                votes
                for _, votes in sorted_positions[5:]
            )

            others_percentage = round(
                (others_votes / total_position_votes) * 100,
                1
            )

            top_positions.append({
                "name": "Others",
                "votes": others_votes,
                "percentage": others_percentage,
                "color": "#94a3b8",
            })

    # ---------------------------------------------------------
    # PER-ELECTION VOTER PARTICIPATION
    # ---------------------------------------------------------

    election_participation = {}

    for election in elections:

        eligible_count = ElectionVoter.query.filter_by(
            election_id=election.id,
            status="eligible"
        ).count()

        voted_count = ElectionVoter.query.filter_by(
            election_id=election.id,
            status="eligible",
            has_voted=True
        ).count()

        yet_to_vote = max(
            eligible_count - voted_count,
            0
        )

        turnout = (
            (voted_count / eligible_count) * 100
            if eligible_count
            else 0
        )

        election_participation[election.id] = {
            "eligible": eligible_count,
            "voted": voted_count,
            "yet_to_vote": yet_to_vote,
            "turnout": round(turnout, 1)
        }



    return render_template(
        "admin/dashboard.html",
        elections=elections,
        voters=voters,
        candidates=candidates,
        ballots=ballots,
        election_participation=election_participation,
        active_elections=active_elections,
        total_elections=len(elections),
        total_voters=len(voters),
        voters_who_voted=voters_who_voted,
        voters_yet_to_vote=voters_yet_to_vote,
        voter_turnout=round(voter_turnout, 1),
        total_candidates=len(candidates),
        total_votes=len(ballots),
        top_positions=top_positions,
    )

@admin_bp.route("/institution")
@login_required
def institution():

    institution = Institution.query.filter_by(
        id=current_user.institution_id
    ).first_or_404()

    return render_template(
        "admin/institution.html",
        institution=institution
    )

@admin_bp.route("/institution/edit", methods=["GET", "POST"])
@login_required
def edit_institution():

    institution = Institution.query.filter_by(
        id=current_user.institution_id
    ).first_or_404()

    if request.method == "POST":

        logo_file = request.files.get("logo")

        name = request.form.get(
            "name",
            ""
        ).strip()

        code = request.form.get(
            "code",
            ""
        ).strip().upper()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        primary_color = request.form.get(
            "primary_color",
            "#0d6efd"
        ).strip()

        secondary_color = request.form.get(
            "secondary_color",
            "#ffffff"
        ).strip()

        # -----------------------------
        # VALIDATION
        # -----------------------------

        if not name:
            flash(
                "Institution name is required.",
                "danger"
            )

            return render_template(
                "admin/institution_edit.html",
                institution=institution
            )

        if not code:
            flash(
                "Institution code is required.",
                "danger"
            )

            return render_template(
                "admin/institution_edit.html",
                institution=institution
            )

        # Check whether another institution
        # is already using this code.
        existing = Institution.query.filter(
            Institution.code == code,
            Institution.id != institution.id
        ).first()

        if existing:
            flash(
                "That institution code is already in use.",
                "danger"
            )

            return render_template(
                "admin/institution_edit.html",
                institution=institution
            )

        try:

            institution.name = name
            institution.code = code
            institution.email = email or None
            institution.phone = phone or None
            institution.address = address or None
            institution.primary_color = (
                primary_color or "#0d6efd"
            )
            institution.secondary_color = (
                secondary_color or "#ffffff"
            )

            # -----------------------------
            # HANDLE INSTITUTION LOGO
            # -----------------------------

            if logo_file and logo_file.filename:

                allowed_extensions = {
                    "png",
                    "jpg",
                    "jpeg",
                    "webp"
                }

                extension = (
                    logo_file.filename
                    .rsplit(".", 1)[-1]
                    .lower()
                )

                if extension not in allowed_extensions:
                    flash(
                        "Invalid logo format. "
                        "Use PNG, JPG, JPEG or WEBP.",
                        "danger"
                    )

                    return render_template(
                        "admin/institution_edit.html",
                        institution=institution
                    )

                filename = secure_filename(
                    logo_file.filename
                )

                # Make filename unique
                filename = (
                    f"institution_{institution.id}_logo."
                    f"{extension}"
                )

                upload_folder = current_app.config[
                    "UPLOAD_FOLDER"
                ]

                os.makedirs(
                    upload_folder,
                    exist_ok=True
                )

                logo_path = os.path.join(
                    upload_folder,
                    filename
                )

                logo_file.save(logo_path)

                # Store the relative path
                institution.logo = filename


            db.session.commit()

            flash(
                "Institution information updated successfully.",
                "success"
            )

            return redirect(
                url_for("admin.institution")
            )

        except Exception as exc:

            db.session.rollback()

            flash(
                f"Could not update institution: {exc}",
                "danger"
            )

    return render_template(
        "admin/institution_edit.html",
        institution=institution
    )

@admin_bp.route("/settings")
@login_required
def settings():

    return render_template(
        "admin/settings.html"
    )


@admin_bp.route("/administrators")
@login_required
def administrators():

    administrators = User.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(
        User.created_at.asc()
    ).all()

    return render_template(
        "admin/administrators.html",
        administrators=administrators
    )


@admin_bp.route("/administrators/add", methods=["GET", "POST"])
@login_required
def add_administrator():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        role = request.form.get(
            "role",
            "admin"
        ).strip().lower()

        status = request.form.get(
            "status",
            "active"
        ).strip().lower()

        # -----------------------------
        # VALIDATION
        # -----------------------------

        if not name:
            flash(
                "Administrator name is required.",
                "danger"
            )

            return render_template(
                "admin/administrator_add.html"
            )

        if not email:
            flash(
                "Administrator email is required.",
                "danger"
            )

            return render_template(
                "admin/administrator_add.html"
            )

        if len(password) < 8:
            flash(
                "Password must be at least 8 characters.",
                "danger"
            )

            return render_template(
                "admin/administrator_add.html"
            )

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "admin/administrator_add.html"
            )

        # Only allow the role currently supported
        # by the administration system.
        if role != "admin":
            flash(
                "Invalid administrator role.",
                "danger"
            )

            return render_template(
                "admin/administrator_add.html"
            )

        if status not in ["active", "inactive"]:
            status = "active"

        # -----------------------------
        # UNIQUE EMAIL
        # -----------------------------

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                "That email address is already registered.",
                "danger"
            )

            return render_template(
                "admin/administrator_add.html"
            )

        try:

            administrator = User(
                institution_id=current_user.institution_id,
                name=name,
                email=email,
                role="admin",
                status=status
            )

            administrator.set_password(password)

            db.session.add(administrator)
            db.session.commit()

            flash(
                f"Administrator {name} was added successfully.",
                "success"
            )

            return redirect(
                url_for("admin.administrators")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Administrator could not be created. "
                "Please try again.",
                "danger"
            )

    return render_template(
        "admin/administrator_add.html"
    )


@admin_bp.route(
    "/administrators/<int:user_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_administrator(user_id):

    administrator = User.query.filter_by(
        id=user_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        role = request.form.get(
            "role",
            "admin"
        ).strip().lower()

        status = request.form.get(
            "status",
            "active"
        ).strip().lower()

        if not name:
            flash(
                "Administrator name is required.",
                "danger"
            )

            return render_template(
                "admin/administrator_edit.html",
                administrator=administrator
            )

        if not email:
            flash(
                "Administrator email is required.",
                "danger"
            )

            return render_template(
                "admin/administrator_edit.html",
                administrator=administrator
            )

        # Check that another user is not using
        # this email address.
        existing_user = User.query.filter(
            User.email == email,
            User.id != administrator.id
        ).first()

        if existing_user:
            flash(
                "That email address is already registered.",
                "danger"
            )

            return render_template(
                "admin/administrator_edit.html",
                administrator=administrator
            )

        if role != "admin":
            flash(
                "Invalid administrator role.",
                "danger"
            )

            return render_template(
                "admin/administrator_edit.html",
                administrator=administrator
            )

        if status not in ["active", "inactive"]:
            status = "active"

        # Prevent the currently logged-in administrator
        # from accidentally disabling their own account.
        if administrator.id == current_user.id:
            status = "active"

        try:

            administrator.name = name
            administrator.email = email
            administrator.role = "admin"
            administrator.status = status

            db.session.commit()

            flash(
                "Administrator information updated successfully.",
                "success"
            )

            return redirect(
                url_for("admin.administrators")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Administrator could not be updated.",
                "danger"
            )

    return render_template(
        "admin/administrator_edit.html",
        administrator=administrator
    )

@admin_bp.route(
    "/administrators/<int:user_id>/change-password",
    methods=["GET", "POST"]
)
@login_required
def change_administrator_password(user_id):

    administrator = User.query.filter_by(
        id=user_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Current password must be correct.
        if not administrator.check_password(current_password):
            flash(
                "Current password is incorrect.",
                "danger"
            )

            return render_template(
                "admin/change_administrator_password.html",
                administrator=administrator
            )

        if len(new_password) < 8:
            flash(
                "New password must be at least 8 characters.",
                "danger"
            )

            return render_template(
                "admin/change_administrator_password.html",
                administrator=administrator
            )

        if new_password != confirm_password:
            flash(
                "New passwords do not match.",
                "danger"
            )

            return render_template(
                "admin/change_administrator_password.html",
                administrator=administrator
            )

        try:

            administrator.set_password(new_password)

            db.session.commit()

            flash(
                "Administrator password changed successfully.",
                "success"
            )

            return redirect(
                url_for("admin.administrators")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Password could not be changed.",
                "danger"
            )

    return render_template(
        "admin/change_administrator_password.html",
        administrator=administrator
    )


@admin_bp.route(
    "/administrators/<int:user_id>/toggle-status",
    methods=["POST"]
)
@login_required
def toggle_administrator_status(user_id):

    administrator = User.query.filter_by(
        id=user_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    # Prevent an administrator from disabling
    # their own currently logged-in account.
    if administrator.id == current_user.id:

        flash(
            "You cannot deactivate your own administrator account.",
            "warning"
        )

        return redirect(
            url_for("admin.administrators")
        )

    if administrator.status == "active":

        administrator.status = "inactive"

        message = (
            f"{administrator.name} has been "
            "deactivated successfully."
        )

    else:

        administrator.status = "active"

        message = (
            f"{administrator.name} has been "
            "activated successfully."
        )

    try:

        db.session.commit()

        flash(
            message,
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Administrator status could not be changed.",
            "danger"
        )

    return redirect(
        url_for("admin.administrators")
    )


@admin_bp.route("/activity-logs")
@login_required
def activity_logs():

    from models import AuditLog

    logs = AuditLog.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(
        AuditLog.created_at.desc()
    ).all()

    return render_template(
        "admin/activity_logs.html",
        logs=logs
    )