import secrets
import string

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
from models import (
    Voter,
    ElectionVoter
)


voters_bp = Blueprint(
    "voters",
    __name__,
    url_prefix="/admin/voters"
)


def generate_voter_id():
    """Generate a unique Universal Voter ID."""

    last_voter = Voter.query.order_by(
        Voter.id.desc()
    ).first()

    if last_voter:
        next_number = last_voter.id + 1
    else:
        next_number = 1

    while True:

        voter_id = f"UV-{next_number:06d}"

        existing = Voter.query.filter_by(
            voter_identifier=voter_id
        ).first()

        if not existing:
            return voter_id

        next_number += 1


def generate_password():
    """Generate a secure voter password."""

    characters = string.ascii_uppercase + string.digits

    while True:

        password = "".join(
            secrets.choice(characters)
            for _ in range(8)
        )

        # Make the password easier to read.
        # Example: K7M4-X9PQ
        password = (
            password[:4]
            + "-"
            + password[4:]
        )

        return password


@voters_bp.route("/")
@login_required
def index():

    voters = Voter.query.filter_by(
        institution_id=current_user.institution_id
    ).order_by(
        Voter.id.desc()
    ).all()

    return render_template(
        "admin/voters/index.html",
        voters=voters
    )



@voters_bp.route(
    "/<int:voter_id>/delete",
    methods=["POST"]
)
@login_required
def delete(voter_id):

    voter = Voter.query.filter_by(
        id=voter_id,
        institution_id=current_user.institution_id
    ).first()

    if not voter:

        flash(
            "Voter account was not found.",
            "danger"
        )

        return redirect(
            url_for("voters.index")
        )


    # Check whether the voter has voted
    voted_entry = ElectionVoter.query.filter_by(
        voter_id=voter.id,
        has_voted=True
    ).first()


    if voted_entry:

        flash(
            f"{voter.voter_identifier} cannot be deleted "
            "because this voter has already voted.",
            "warning"
        )

        return redirect(
            url_for("voters.index")
        )


    voter_identifier = voter.voter_identifier

    try:

        db.session.delete(voter)

        db.session.commit()

        flash(
            f"Voter {voter_identifier} was deleted successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "The voter could not be deleted.",
            "danger"
        )


    return redirect(
        url_for("voters.index")
    )


@voters_bp.route(
    "/delete-all",
    methods=["POST"]
)
@login_required
def delete_all():

    voters = Voter.query.filter_by(
        institution_id=current_user.institution_id
    ).all()


    if not voters:

        flash(
            "There are no voters to delete.",
            "info"
        )

        return redirect(
            url_for("voters.index")
        )


    # Check whether any voter has already voted
    voter_ids = [
        voter.id
        for voter in voters
    ]


    voted_count = ElectionVoter.query.filter(
        ElectionVoter.voter_id.in_(voter_ids),
        ElectionVoter.has_voted == True
    ).count()


    if voted_count > 0:

        flash(
            f"Delete All was cancelled. "
            f"{voted_count} voter account(s) have already voted "
            "and cannot be deleted.",
            "warning"
        )

        return redirect(
            url_for("voters.index")
        )


    deleted_count = len(voters)


    try:

        for voter in voters:

            db.session.delete(voter)

        db.session.commit()

        flash(
            f"{deleted_count} voter account(s) "
            "were deleted successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "The voter accounts could not be deleted.",
            "danger"
        )


    return redirect(
        url_for("voters.index")
    )





@voters_bp.route(
    "/create",
    methods=["GET", "POST"]
)
@login_required
def create():

    if request.method == "POST":

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        # Generate credentials automatically.
        voter_identifier = generate_voter_id()
        temporary_password = generate_password()

        voter = Voter(
            institution_id=current_user.institution_id,
            voter_identifier=voter_identifier,
            name=voter_identifier,
            phone=phone or None,
            status="active"
        )

        voter.set_password(
            temporary_password
        )

        db.session.add(voter)
        db.session.commit()

        return render_template(
            "admin/voters/credentials.html",
            voter=voter,
            temporary_password=temporary_password
        )

    return render_template(
        "admin/voters/create.html"
    )


@voters_bp.route(
    "/bulk-create",
    methods=["GET", "POST"]
)
@login_required
def bulk_create():

    if request.method == "POST":

        raw_numbers = request.form.get(
            "phone_numbers",
            ""
        )

        # Split entries entered one per line
        voter_entries = [
            entry.strip()
            for entry in raw_numbers.splitlines()
            if entry.strip()
        ]

        if not voter_entries:

            flash(
                "Please enter at least one phone number.",
                "warning"
            )

            return render_template(
                "admin/voters/bulk_create.html"
            )

        created_voters = []
        duplicates = []
        invalid_numbers = []

        # Remove duplicate entries from the submitted list
        # Remove duplicate phone numbers,
        # but keep every NO PHONE entry.
        unique_entries = []

        seen_phones = set()

        for entry in voter_entries:

            normalized = entry.strip().upper()

            if normalized in {
                "NO PHONE",
                "NO-PHONE",
                "NOPHONE",
                "N/A",
                "NA",
                "NONE",
            }:
                unique_entries.append(entry)
                continue

            if entry not in seen_phones:
                seen_phones.add(entry)
                unique_entries.append(entry)
        for entry in unique_entries:

            # -------------------------------------------------
            # VOTER WITHOUT PHONE NUMBER
            # -------------------------------------------------

            no_phone_values = {
                "NO PHONE",
                "NO-PHONE",
                "NOPHONE",
                "N/A",
                "NA",
                "NONE",
            }

            if entry.upper() in no_phone_values:

                phone = None

            else:

                # ---------------------------------------------
                # NORMAL PHONE NUMBER
                # ---------------------------------------------

                cleaned_phone = (
                    entry
                    .replace(" ", "")
                    .replace("-", "")
                    .replace("(", "")
                    .replace(")", "")
                )

                if not cleaned_phone.isdigit():
                    invalid_numbers.append(entry)
                    continue

                if len(cleaned_phone) < 9:
                    invalid_numbers.append(entry)
                    continue

                phone = entry

                # Check if phone already exists
                existing = Voter.query.filter_by(
                    institution_id=current_user.institution_id,
                    phone=phone
                ).first()

                if existing:
                    duplicates.append(phone)
                    continue

            # -------------------------------------------------
            # GENERATE LOGIN CREDENTIALS
            # -------------------------------------------------

            voter_identifier = generate_voter_id()

            temporary_password = generate_password()

            voter = Voter(
                institution_id=current_user.institution_id,
                voter_identifier=voter_identifier,
                name=f"Voter {voter_identifier}",
                phone=phone,
                status="active"
            )

            voter.set_password(
                temporary_password
            )

            db.session.add(voter)

            created_voters.append({
                "phone": phone or "Not provided",
                "voter_identifier": voter_identifier,
                "password": temporary_password
            })

            if not cleaned_phone.isdigit():

                invalid_numbers.append(phone)
                continue

            if len(cleaned_phone) < 9:

                invalid_numbers.append(phone)
                continue

            # Check if phone already exists
            existing = Voter.query.filter_by(
                institution_id=current_user.institution_id,
                phone=phone
            ).first()

            if existing:

                duplicates.append(phone)
                continue

            # Generate credentials
            voter_identifier = generate_voter_id()
            temporary_password = generate_password()

            voter = Voter(
                institution_id=current_user.institution_id,
                voter_identifier=voter_identifier,
                name=f"Voter {voter_identifier}",
                phone=phone,
                status="active"
            )

            voter.set_password(
                temporary_password
            )

            db.session.add(voter)

            created_voters.append({
                "phone": phone,
                "voter_identifier": voter_identifier,
                "password": temporary_password
            })

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "The bulk voter registration failed. "
                "No accounts were created.",
                "danger"
            )

            return redirect(
                url_for(
                    "voters.bulk_create"
                )
            )

        return render_template(
            "admin/voters/bulk_credentials.html",
            created_voters=created_voters,
            duplicates=duplicates,
            invalid_numbers=invalid_numbers
        )

    return render_template(
        "admin/voters/bulk_create.html"
    )

@voters_bp.route(
    "/generate-accounts",
    methods=["GET", "POST"]
)
@login_required
def generate_accounts():

    if request.method == "POST":

        try:
            count = int(
                request.form.get(
                    "count",
                    0
                )
            )
        except (TypeError, ValueError):

            flash(
                "Please enter a valid number of accounts.",
                "danger"
            )

            return redirect(
                url_for(
                    "voters.generate_accounts"
                )
            )


        # Safety limit
        if count < 1 or count > 5000:

            flash(
                "Please enter a number between 1 and 5000.",
                "warning"
            )

            return redirect(
                url_for(
                    "voters.generate_accounts"
                )
            )


        created_voters = []


        for _ in range(count):

            voter_identifier = generate_voter_id()

            temporary_password = generate_password()


            voter = Voter(
                institution_id=current_user.institution_id,
                voter_identifier=voter_identifier,
                name=f"Voter {voter_identifier}",
                phone=None,
                status="active"
            )


            voter.set_password(
                temporary_password
            )


            db.session.add(voter)


            created_voters.append({
                "voter_identifier": voter_identifier,
                "password": temporary_password
            })


        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Account generation failed. "
                "No accounts were created.",
                "danger"
            )

            return redirect(
                url_for(
                    "voters.generate_accounts"
                )
            )


        return render_template(
            "admin/voters/generated_accounts.html",
            created_voters=created_voters
        )


    return render_template(
        "admin/voters/generate_accounts.html"
    )