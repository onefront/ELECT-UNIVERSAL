from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from services.audit_service import log_activity
from flask_login import login_required, current_user

from extensions import db
from models import (
    Election,
    ElectionSettings,
    Voter,
    ElectionVoter,
    Position,
    Candidate,
    Ballot,
    BallotSelection
)


elections_bp = Blueprint(
    "elections",
    __name__,
    url_prefix="/admin/elections"
)


@elections_bp.route("/")
@login_required
def index():

    elections = Election.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(
        Election.created_at.desc()
    ).all()

    return render_template(
        "admin/elections/index.html",
        elections=elections
    )


@elections_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        start_date = request.form.get(
            "start_date",
            ""
        ).strip()

        start_time = request.form.get(
            "start_time",
            ""
        ).strip()

        end_date = request.form.get(
            "end_date",
            ""
        ).strip()

        end_time = request.form.get(
            "end_time",
            ""
        ).strip()

        require_voter_verification = (
            request.form.get("require_voter_verification")
            == "on"
        )

        show_candidate_manifesto = (
            request.form.get("show_candidate_manifesto")
            == "on"
        )

        show_results_before_close = (
            request.form.get("show_results_before_close")
            == "on"
        )

        allow_abstain = (
            request.form.get("allow_abstain")
            == "on"
        )

        # Basic validation

        if not name:
            flash(
                "Election name is required.",
                "danger"
            )

            return render_template(
                "admin/elections/create.html"
            )

        if not start_date or not start_time:
            flash(
                "Election start date and time are required.",
                "danger"
            )

            return render_template(
                "admin/elections/create.html"
            )

        if not end_date or not end_time:
            flash(
                "Election end date and time are required.",
                "danger"
            )

            return render_template(
                "admin/elections/create.html"
            )

        try:

            start_datetime = datetime.strptime(
                f"{start_date} {start_time}",
                "%Y-%m-%d %H:%M"
            )

            end_datetime = datetime.strptime(
                f"{end_date} {end_time}",
                "%Y-%m-%d %H:%M"
            )

        except ValueError:

            flash(
                "Please enter valid dates and times.",
                "danger"
            )

            return render_template(
                "admin/elections/create.html"
            )

        if end_datetime <= start_datetime:

            flash(
                "Election end time must be after the start time.",
                "danger"
            )

            return render_template(
                "admin/elections/create.html"
            )

        try:

            election = Election(
                institution_id=current_user.institution_id,
                name=name,
                description=description or None,
                start_date=start_datetime,
                end_date=end_datetime,
                status="draft",
            )

            db.session.add(election)

            # Flush so the election receives its ID
            db.session.flush()

            settings = ElectionSettings(
                election_id=election.id,
                require_voter_verification=(
                    require_voter_verification
                ),
                show_candidate_manifesto=(
                    show_candidate_manifesto
                ),
                show_results_before_close=(
                    show_results_before_close
                ),
                allow_abstain=allow_abstain,
            )

            db.session.add(settings)

            db.session.commit()

            log_activity(
                action="CREATE ELECTION",
                description=f'Created election "{election.name}".',
                entity_type="Election",
                entity_id=election.id
            )



            flash(
                "Election created successfully.",
                "success"
            )

            return redirect(
                url_for(
                    "elections.view",
                    election_id=election.id
                )
            )

        except Exception:

            db.session.rollback()

            flash(
                "The election could not be created. "
                "Please try again.",
                "danger"
            )

    return render_template(
        "admin/elections/create.html"
    )


@elections_bp.route("/<int:election_id>")
@login_required
def view(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    return render_template(
        "admin/elections/view.html",
        election=election
    )



@elections_bp.route(
    "/<int:election_id>/status",
    methods=["POST"]
)
@login_required
def update_status(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    new_status = request.form.get(
        "status",
        ""
    ).strip().lower()

    allowed_transitions = {
        "draft": ["active"],
        "active": ["closed"],
        "closed": []
    }

    if new_status not in allowed_transitions.get(
        election.status,
        []
    ):
        flash(
            "Invalid election status change.",
            "danger"
        )

        return redirect(
            url_for(
                "elections.view",
                election_id=election.id
            )
        )

    election.status = new_status

    db.session.commit()

    if new_status == "active":

        flash(
            "Election launched successfully. Voting is now open.",
            "success"
        )

    elif new_status == "closed":

        flash(
            "Election closed successfully.",
            "success"
        )

    return redirect(
        url_for(
            "elections.view",
            election_id=election.id
        )
    )



@elections_bp.route(
    "/<int:election_id>/delete",
    methods=["POST"]
)
@login_required
def delete(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    # Never allow an active election to be deleted.
    if election.status == "active":
        flash(
            "Active elections cannot be deleted. "
            "Close the election first.",
            "danger"
        )

        return redirect(
            url_for(
                "elections.view",
                election_id=election.id
            )
        )

    try:

        # -----------------------------------------
        # DELETE BALLOT SELECTIONS
        # -----------------------------------------

        ballots = Ballot.query.filter_by(
            election_id=election.id
        ).all()

        for ballot in ballots:

            BallotSelection.query.filter_by(
                ballot_id=ballot.id
            ).delete(
                synchronize_session=False
            )

        # -----------------------------------------
        # DELETE BALLOTS
        # -----------------------------------------

        Ballot.query.filter_by(
            election_id=election.id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------
        # REMEMBER VOTERS LINKED TO THIS ELECTION
        # -----------------------------------------

        linked_voter_ids = [
            entry.voter_id
            for entry in ElectionVoter.query.filter_by(
                election_id=election.id
            ).all()
        ]

        # -----------------------------------------
        # DELETE ELECTION VOTERS
        # -----------------------------------------

        ElectionVoter.query.filter_by(
            election_id=election.id
        ).delete(
            synchronize_session=False
        )


        # -----------------------------------------
        # DELETE UNUSED VOTER ACCOUNTS
        # -----------------------------------------

        deleted_voter_count = 0

        for voter_id in linked_voter_ids:

            still_linked = ElectionVoter.query.filter_by(
                voter_id=voter_id
            ).first()

            if not still_linked:

                voter = db.session.get(
                    Voter,
                    voter_id
                )

                if voter:

                    db.session.delete(voter)

                    deleted_voter_count += 1



        # -----------------------------------------
        # DELETE CANDIDATES
        # -----------------------------------------

        Candidate.query.filter_by(
            election_id=election.id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------
        # DELETE POSITIONS
        # -----------------------------------------

        Position.query.filter_by(
            election_id=election.id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------
        # DELETE ELECTION SETTINGS
        # -----------------------------------------

        ElectionSettings.query.filter_by(
            election_id=election.id
        ).delete(
            synchronize_session=False
        )

        election_name = election.name

        # -----------------------------------------
        # DELETE ELECTION
        # -----------------------------------------

        db.session.delete(election)

        db.session.commit()

        flash(
            f'Election "{election_name}" was deleted successfully. '
            f'{deleted_voter_count} unused voter account(s) were removed.',
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "The election could not be deleted. "
            "No changes were made.",
            "danger"
        )

    return redirect(
        url_for("elections.index")
    )





@elections_bp.route(
    "/<int:election_id>/voters",
    methods=["GET", "POST"]
)
@login_required
def voters(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    if request.method == "POST":

        selected_voter_ids = request.form.getlist(
            "voter_ids"
        )

        if not selected_voter_ids:

            flash(
                "Please select at least one voter.",
                "warning"
            )

            return redirect(
                url_for(
                    "elections.voters",
                    election_id=election.id
                )
            )

        assigned_count = 0

        for voter_id in selected_voter_ids:

            try:
                voter_id = int(voter_id)
            except ValueError:
                continue

            voter = Voter.query.filter_by(
                id=voter_id,
                institution_id=current_user.institution_id
            ).first()

            if not voter:
                continue

            existing = ElectionVoter.query.filter_by(
                election_id=election.id,
                voter_id=voter.id
            ).first()

            if existing:
                continue

            election_voter = ElectionVoter(
                election_id=election.id,
                voter_id=voter.id,
                status="eligible",
                has_voted=False
            )

            db.session.add(
                election_voter
            )

            assigned_count += 1

        db.session.commit()

        flash(
            f"{assigned_count} voter(s) assigned successfully.",
            "success"
        )

        return redirect(
            url_for(
                "elections.voters",
                election_id=election.id
            )
        )

    all_voters = Voter.query.filter_by(
        institution_id=current_user.institution_id,
        status="active"
    ).order_by(
        Voter.id.asc()
    ).all()

    assigned_entries = ElectionVoter.query.filter_by(
        election_id=election.id
    ).all()

    assigned_voter_ids = {
        entry.voter_id
        for entry in assigned_entries
    }

    return render_template(
        "admin/elections/voters.html",
        election=election,
        voters=all_voters,
        assigned_voter_ids=assigned_voter_ids,
        assigned_entries=assigned_entries
    )



@elections_bp.route("/results")
@login_required
def results_index():

    elections = Election.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(
        Election.created_at.desc()
    ).all()

    return render_template(
        "admin/elections/results_index.html",
        elections=elections
    )



@elections_bp.route(
    "/<int:election_id>/results"
)
@login_required
def results(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    # ---------------------------------------------------------
    # VOTER STATISTICS
    # ---------------------------------------------------------

    total_voters = ElectionVoter.query.filter_by(
        election_id=election.id,
        status="eligible"
    ).count()

    votes_cast = ElectionVoter.query.filter_by(
        election_id=election.id,
        status="eligible",
        has_voted=True
    ).count()

    if total_voters > 0:
        turnout_percentage = (
            votes_cast / total_voters
        ) * 100
    else:
        turnout_percentage = 0


    # ---------------------------------------------------------
    # POSITIONS AND CANDIDATE RESULTS
    # ---------------------------------------------------------

    positions = Position.query.filter_by(
        election_id=election.id
    ).order_by(
        Position.display_order.asc(),
        Position.id.asc()
    ).all()

    results_data = []

    for position in positions:

        candidates = Candidate.query.filter_by(
            election_id=election.id,
            position_id=position.id
        ).order_by(
            Candidate.created_at.asc()
        ).all()

        candidate_results = []

        for candidate in candidates:

            vote_count = (
                BallotSelection.query
                .join(
                    Ballot,
                    BallotSelection.ballot_id == Ballot.id
                )
                .filter(
                    Ballot.election_id == election.id,
                    BallotSelection.position_id == position.id,
                    BallotSelection.candidate_id == candidate.id
                )
                .count()
            )

            if votes_cast > 0:
                percentage = (
                    vote_count / votes_cast
                ) * 100
            else:
                percentage = 0

            candidate_results.append({
                "candidate": candidate,
                "votes": vote_count,
                "percentage": percentage
            })


        # Determine highest vote count
        highest_votes = max(
            [item["votes"] for item in candidate_results],
            default=0
        )

        for item in candidate_results:

            item["is_winner"] = (
                highest_votes > 0
                and item["votes"] == highest_votes
            )


        results_data.append({
            "position": position,
            "candidates": candidate_results
        })


    return render_template(
        "admin/elections/results.html",
        election=election,
        total_voters=total_voters,
        votes_cast=votes_cast,
        turnout_percentage=turnout_percentage,
        results_data=results_data
    )



@elections_bp.route(
    "/<int:election_id>/publish-results",
    methods=["POST"]
)
@login_required
def publish_results(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    # Results should only be published after the election is closed.
    if election.status != "closed":

        flash(
            "Results can only be published after the election is closed.",
            "warning"
        )

        return redirect(
            url_for(
                "elections.results",
                election_id=election.id
            )
        )

    settings = ElectionSettings.query.filter_by(
        election_id=election.id
    ).first()

    if not settings:

        flash(
            "Election settings could not be found.",
            "danger"
        )

        return redirect(
            url_for(
                "elections.results",
                election_id=election.id
            )
        )

    if settings.results_published:

        flash(
            "The election results have already been published.",
            "info"
        )

        return redirect(
            url_for(
                "elections.results",
                election_id=election.id
            )
        )

    try:

        settings.results_published = True

        db.session.commit()

        log_activity(
            action="PUBLISH RESULTS",
            description=(
                f'Published results for election '
                f'"{election.name}".'
            ),
            entity_type="Election",
            entity_id=election.id
        )

        flash(
            f'Results for "{election.name}" have been published successfully.',
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "The election results could not be published.",
            "danger"
        )

    return redirect(
        url_for(
            "elections.results",
            election_id=election.id
        )
    )





@elections_bp.route("/reports")
@login_required
def reports_index():

    elections = Election.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(
        Election.created_at.desc()
    ).all()

    return render_template(
        "admin/elections/reports_index.html",
        elections=elections
    )


@elections_bp.route("/<int:election_id>/report")
@login_required
def election_report(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    # -----------------------------
    # VOTER STATISTICS
    # -----------------------------

    total_voters = ElectionVoter.query.filter_by(
        election_id=election.id,
        status="eligible"
    ).count()

    votes_cast = ElectionVoter.query.filter_by(
        election_id=election.id,
        status="eligible",
        has_voted=True
    ).count()

    turnout_percentage = (
        (votes_cast / total_voters) * 100
        if total_voters > 0
        else 0
    )

    # -----------------------------
    # POSITIONS & CANDIDATES
    # -----------------------------

    positions = Position.query.filter_by(
        election_id=election.id
    ).order_by(
        Position.display_order.asc(),
        Position.id.asc()
    ).all()

    report_data = []

    total_candidates = 0

    for position in positions:

        candidates = Candidate.query.filter_by(
            election_id=election.id,
            position_id=position.id
        ).order_by(
            Candidate.created_at.asc()
        ).all()

        candidate_results = []

        for candidate in candidates:

            vote_count = (
                BallotSelection.query
                .join(
                    Ballot,
                    BallotSelection.ballot_id == Ballot.id
                )
                .filter(
                    Ballot.election_id == election.id,
                    BallotSelection.position_id == position.id,
                    BallotSelection.candidate_id == candidate.id
                )
                .count()
            )

            percentage = (
                (vote_count / votes_cast) * 100
                if votes_cast > 0
                else 0
            )

            candidate_results.append({
                "candidate": candidate,
                "votes": vote_count,
                "percentage": percentage
            })

        total_candidates += len(candidate_results)

        highest_votes = max(
            [item["votes"] for item in candidate_results],
            default=0
        )

        for item in candidate_results:

            item["is_winner"] = (
                highest_votes > 0
                and item["votes"] == highest_votes
            )

        report_data.append({
            "position": position,
            "candidates": candidate_results
        })

    return render_template(
        "admin/elections/report.html",
        election=election,
        total_voters=total_voters,
        votes_cast=votes_cast,
        turnout_percentage=turnout_percentage,
        total_positions=len(positions),
        total_candidates=total_candidates,
        report_data=report_data
    )