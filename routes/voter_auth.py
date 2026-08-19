from services.audit_service import log_activity
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
)

from extensions import db
from models import (
    Voter,
    ElectionVoter,
    Position,
    Candidate,
    Ballot,
    BallotSelection,
ElectionSettings
)


voter_auth_bp = Blueprint(
    "voter_auth",
    __name__,
    url_prefix="/voter"
)


@voter_auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        voter_identifier = request.form.get(
            "voter_identifier",
            ""
        ).strip().upper()

        password = request.form.get(
            "password",
            ""
        )

        if not voter_identifier or not password:

            flash(
                "Voter ID and password are required.",
                "danger"
            )

            return render_template(
                "voter/login.html"
            )

        voter = Voter.query.filter_by(
            voter_identifier=voter_identifier
        ).first()

        if not voter:

            flash(
                "Invalid Voter ID or password.",
                "danger"
            )

            return render_template(
                "voter/login.html"
            )

        if voter.status != "active":

            flash(
                "This voter account is inactive.",
                "danger"
            )

            return render_template(
                "voter/login.html"
            )

        if not voter.password_hash:

            flash(
                "This voter account has no password.",
                "danger"
            )

            return render_template(
                "voter/login.html"
            )

        from werkzeug.security import check_password_hash

        if not check_password_hash(
            voter.password_hash,
            password
        ):

            flash(
                "Invalid Voter ID or password.",
                "danger"
            )

            return render_template(
                "voter/login.html"
            )

        # Store voter session
        session["voter_id"] = voter.id
        session["voter_identifier"] = voter.voter_identifier

        log_activity(
            action="VOTER LOGIN",
            description=(
                f'Voter {voter.voter_identifier} '
                f'logged into the voting system.'
            ),
            entity_type="Voter",
            entity_id=voter.id,
            voter=voter
        )

        return redirect(
            url_for(
                "voter_auth.dashboard"
            )
        )

    return render_template(
        "voter/login.html"
    )


@voter_auth_bp.route("/dashboard")
def dashboard():

    voter_id = session.get("voter_id")

    if not voter_id:
        return redirect(
            url_for("voter_auth.login")
        )

    voter = db.session.get(
        Voter,
        voter_id
    )

    if not voter:
        session.clear()

        return redirect(
            url_for("voter_auth.login")
        )

    # Get elections assigned to this voter
    election_entries = ElectionVoter.query.filter_by(
        voter_id=voter.id,
        status="eligible"
    ).order_by(
        ElectionVoter.created_at.desc()
    ).all()

    return render_template(
        "voter/dashboard.html",
        voter=voter,
        election_entries=election_entries
    )


@voter_auth_bp.route("/election/<int:election_id>")
def election_view(election_id):

    voter_id = session.get("voter_id")

    if not voter_id:
        return redirect(
            url_for("voter_auth.login")
        )

    voter = db.session.get(
        Voter,
        voter_id
    )

    if not voter:
        session.clear()

        return redirect(
            url_for("voter_auth.login")
        )

    # Make sure this voter is assigned to this election
    election_entry = ElectionVoter.query.filter_by(
        election_id=election_id,
        voter_id=voter.id,
        status="eligible"
    ).first()

    if not election_entry:

        flash(
            "You are not eligible to access this election.",
            "danger"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    election = election_entry.election

    return render_template(
        "voter/election.html",
        voter=voter,
        election=election,
        election_entry=election_entry
    )



@voter_auth_bp.route("/election/<int:election_id>/results")
def election_results(election_id):

    voter_id = session.get("voter_id")

    if not voter_id:
        return redirect(
            url_for("voter_auth.login")
        )

    voter = db.session.get(
        Voter,
        voter_id
    )

    if not voter:
        session.clear()

        return redirect(
            url_for("voter_auth.login")
        )

    # ---------------------------------------------------------
    # MAKE SURE THIS VOTER IS ASSIGNED TO THIS ELECTION
    # ---------------------------------------------------------

    election_entry = ElectionVoter.query.filter_by(
        election_id=election_id,
        voter_id=voter.id,
        status="eligible"
    ).first()

    if not election_entry:

        flash(
            "You are not eligible to view this election.",
            "danger"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    election = election_entry.election

    # ---------------------------------------------------------
    # RESULTS MUST BE CLOSED AND PUBLISHED
    # ---------------------------------------------------------

    settings = election.settings

    if election.status != "closed":

        return render_template(
            "voter/results_locked.html",
            voter=voter,
            election=election,
            message="Results will be available after the election is closed."
        )

    if not settings or not settings.results_published:

        return render_template(
            "voter/results_locked.html",
            voter=voter,
            election=election,
            message="The election results have not been published yet."
        )

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
    # POSITIONS AND RESULTS
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

        # -----------------------------------------------------
        # DETERMINE WINNER
        # -----------------------------------------------------

        highest_votes = max(
            [
                item["votes"]
                for item in candidate_results
            ],
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
        "voter/results.html",
        voter=voter,
        election=election,
        total_voters=total_voters,
        votes_cast=votes_cast,
        turnout_percentage=turnout_percentage,
        results_data=results_data
    )



@voter_auth_bp.route(
    "/election/<int:election_id>/vote",
    methods=["GET", "POST"]
)
def vote(election_id):

    voter_id = session.get("voter_id")

    if not voter_id:
        return redirect(
            url_for("voter_auth.login")
        )

    voter = db.session.get(
        Voter,
        voter_id
    )

    if not voter:
        session.clear()

        return redirect(
            url_for("voter_auth.login")
        )

    election_entry = ElectionVoter.query.filter_by(
        election_id=election_id,
        voter_id=voter.id,
        status="eligible"
    ).first()

    if not election_entry:

        flash(
            "You are not eligible to vote in this election.",
            "danger"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    election = election_entry.election

    if election.status != "active":

        flash(
            "Voting is not currently open for this election.",
            "warning"
        )

        return redirect(
            url_for(
                "voter_auth.election_view",
                election_id=election.id
            )
        )

    if election_entry.has_voted:

        flash(
            "You have already voted in this election.",
            "warning"
        )

        return redirect(
            url_for(
                "voter_auth.election_view",
                election_id=election.id
            )
        )

    positions = Position.query.filter_by(
        election_id=election.id
    ).order_by(
        Position.display_order.asc(),
        Position.id.asc()
    ).all()

    for position in positions:

        position.active_candidates = Candidate.query.filter_by(
            election_id=election.id,
            position_id=position.id,
            status="active"
        ).order_by(
            Candidate.created_at.asc()
        ).all()


    # ---------------------------------------------------------
    # PROCESS VOTER SELECTIONS
    # ---------------------------------------------------------

    if request.method == "POST":

        selections = {}

        for position in positions:

            field_name = f"position_{position.id}"

            candidate_id = request.form.get(
                field_name
            )

            if not candidate_id:

                flash(
                    f"Please select a candidate for {position.name}.",
                    "warning"
                )

                return render_template(
                    "voter/vote.html",
                    voter=voter,
                    election=election,
                    election_entry=election_entry,
                    positions=positions
                )

            try:

                candidate_id = int(candidate_id)

            except (TypeError, ValueError):

                flash(
                    "Invalid candidate selection.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "voter_auth.vote",
                        election_id=election.id
                    )
                )

            candidate = Candidate.query.filter_by(
                id=candidate_id,
                election_id=election.id,
                position_id=position.id,
                status="active"
            ).first()

            if not candidate:

                flash(
                    "Invalid candidate selection detected.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "voter_auth.vote",
                        election_id=election.id
                    )
                )

            selections[str(position.id)] = {
                "position_id": position.id,
                "position_name": position.name,
                "candidate_id": candidate.id,
                "candidate_name": candidate.name
            }


        # Save selections temporarily in session
        session["vote_selections"] = selections
        session["vote_election_id"] = election.id

        return redirect(
            url_for(
                "voter_auth.review_vote",
                election_id=election.id
            )
        )


    return render_template(
        "voter/vote.html",
        voter=voter,
        election=election,
        election_entry=election_entry,
        positions=positions
    )




@voter_auth_bp.route(
    "/election/<int:election_id>/review",
    methods=["GET"]
)
def review_vote(election_id):

    voter_id = session.get("voter_id")

    if not voter_id:
        return redirect(
            url_for("voter_auth.login")
        )

    voter = db.session.get(
        Voter,
        voter_id
    )

    if not voter:
        session.clear()

        return redirect(
            url_for("voter_auth.login")
        )

    election_entry = ElectionVoter.query.filter_by(
        election_id=election_id,
        voter_id=voter.id,
        status="eligible"
    ).first()

    if not election_entry:

        flash(
            "You are not eligible to vote in this election.",
            "danger"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    if election_entry.has_voted:

        flash(
            "You have already voted in this election.",
            "warning"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    if election_entry.election.status != "active":

        flash(
            "Voting is not currently open.",
            "warning"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    if session.get("vote_election_id") != election_id:

        flash(
            "Your vote selections have expired. Please select your candidates again.",
            "warning"
        )

        return redirect(
            url_for(
                "voter_auth.vote",
                election_id=election_id
            )
        )

    selections = session.get(
        "vote_selections",
        {}
    )

    if not selections:

        flash(
            "Please select your candidates first.",
            "warning"
        )

        return redirect(
            url_for(
                "voter_auth.vote",
                election_id=election_id
            )
        )

    return render_template(
        "voter/review_vote.html",
        voter=voter,
        election=election_entry.election,
        election_entry=election_entry,
        selections=selections
    )


@voter_auth_bp.route(
    "/election/<int:election_id>/confirm-vote",
    methods=["POST"]
)
def confirm_vote(election_id):

    voter_id = session.get("voter_id")

    if not voter_id:
        return redirect(
            url_for("voter_auth.login")
        )

    voter = db.session.get(
        Voter,
        voter_id
    )

    if not voter:
        session.clear()

        return redirect(
            url_for("voter_auth.login")
        )

    election_entry = ElectionVoter.query.filter_by(
        election_id=election_id,
        voter_id=voter.id,
        status="eligible"
    ).first()

    if not election_entry:

        flash(
            "You are not eligible to vote in this election.",
            "danger"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    election = election_entry.election

    # Election must still be active
    if election.status != "active":

        flash(
            "Voting is no longer open for this election.",
            "warning"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    # Prevent duplicate voting
    if election_entry.has_voted:

        flash(
            "You have already voted in this election.",
            "warning"
        )

        return redirect(
            url_for("voter_auth.dashboard")
        )

    # Make sure the temporary selections belong to this election
    if session.get("vote_election_id") != election_id:

        flash(
            "Your vote session has expired. Please vote again.",
            "warning"
        )

        return redirect(
            url_for(
                "voter_auth.vote",
                election_id=election_id
            )
        )

    selections = session.get(
        "vote_selections",
        {}
    )

    if not selections:

        flash(
            "No vote selections were found.",
            "warning"
        )

        return redirect(
            url_for(
                "voter_auth.vote",
                election_id=election_id
            )
        )

    try:

        # Create the ballot
        ballot = Ballot(
            election_id=election.id
        )

        db.session.add(ballot)

        db.session.flush()


        # Validate and record every selection
        for position_id, selection in selections.items():

            position = Position.query.filter_by(
                id=selection["position_id"],
                election_id=election.id
            ).first()

            if not position:
                raise ValueError(
                    "Invalid election position."
                )


            candidate = Candidate.query.filter_by(
                id=selection["candidate_id"],
                election_id=election.id,
                position_id=position.id,
                status="active"
            ).first()

            if not candidate:
                raise ValueError(
                    "Invalid candidate selection."
                )


            ballot_selection = BallotSelection(
                ballot_id=ballot.id,
                position_id=position.id,
                candidate_id=candidate.id
            )

            db.session.add(
                ballot_selection
            )


        # Mark voter as having voted
        election_entry.has_voted = True
        election_entry.voted_at = datetime.utcnow()

        db.session.commit()

        log_activity(
            action="CAST VOTE",
            description=(
                f'Voter {voter.voter_identifier} successfully '
                f'cast a vote in election "{election.name}".'
            ),
            entity_type="Election",
            entity_id=election.id
        )

        # Clear temporary vote data
        session.pop(
            "vote_selections",
            None
        )

        session.pop(
            "vote_election_id",
            None
        )


        return render_template(
            "voter/vote_success.html",
            voter=voter,
            election=election,
            ballot=ballot
        )


    except Exception as e:

        db.session.rollback()

        flash(
            "Your vote could not be submitted. Please try again.",
            "danger"
        )

        return redirect(
            url_for(
                "voter_auth.vote",
                election_id=election.id
            )
        )



@voter_auth_bp.route("/logout")
def logout():

    voter_id = session.get("voter_id")

    if voter_id:

        voter = db.session.get(
            Voter,
            voter_id
        )

        if voter:

            log_activity(
                action="VOTER LOGOUT",
                description=(
                    f'Voter {voter.voter_identifier} '
                    f'logged out of the voting system.'
                ),
                entity_type="Voter",
                entity_id=voter.id,
                voter=voter
            )

    session.pop(
        "voter_id",
        None
    )

    session.pop(
        "voter_identifier",
        None
    )

    return redirect(
        url_for(
            "voter_auth.login"
        )
    )