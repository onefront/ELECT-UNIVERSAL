import os

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)

from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from extensions import db
from models import Election, Position, Candidate


candidates_bp = Blueprint(
    "candidates",
    __name__,
    url_prefix="/admin/elections"
)


@candidates_bp.route("/<int:election_id>/candidates")
@login_required
def index(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    positions = Position.query.filter_by(
        election_id=election.id
    ).order_by(
        Position.display_order.asc(),
        Position.id.asc()
    ).all()

    candidates = Candidate.query.filter_by(
        election_id=election.id
    ).order_by(
        Candidate.created_at.asc()
    ).all()

    return render_template(
        "admin/elections/candidates/index.html",
        election=election,
        positions=positions,
        candidates=candidates
    )


@candidates_bp.route(
    "/<int:election_id>/candidates/create",
    methods=["GET", "POST"]
)
@login_required
def create(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    positions = Position.query.filter_by(
        election_id=election.id
    ).order_by(
        Position.display_order.asc(),
        Position.id.asc()
    ).all()

    if not positions:
        flash(
            "Create at least one position before adding candidates.",
            "warning"
        )

        return redirect(
            url_for(
                "positions.index",
                election_id=election.id
            )
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        position_id = request.form.get(
            "position_id",
            ""
        ).strip()

        manifesto = request.form.get(
            "manifesto",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "active"
        ).strip()

        if not name:

            flash(
                "Candidate name is required.",
                "danger"
            )

            return render_template(
                "admin/elections/candidates/create.html",
                election=election,
                positions=positions
            )

        try:
            position_id = int(position_id)

        except ValueError:

            flash(
                "Please select a valid position.",
                "danger"
            )

            return render_template(
                "admin/elections/candidates/create.html",
                election=election,
                positions=positions
            )

        position = Position.query.filter_by(
            id=position_id,
            election_id=election.id
        ).first()

        if not position:

            flash(
                "The selected position does not belong to this election.",
                "danger"
            )

            return render_template(
                "admin/elections/candidates/create.html",
                election=election,
                positions=positions
            )

        if status not in ["active", "inactive"]:

            status = "active"

        photo_filename = None

        photo = request.files.get("photo")

        if photo and photo.filename:

            filename = secure_filename(
                photo.filename
            )

            upload_folder = os.path.join(
                "static",
                "uploads",
                "candidates"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            photo_filename = filename

            photo.save(
                os.path.join(
                    upload_folder,
                    photo_filename
                )
            )

        candidate = Candidate(
            election_id=election.id,
            position_id=position.id,
            name=name,
            photo=photo_filename,
            manifesto=manifesto or None,
            status=status
        )

        db.session.add(candidate)

        db.session.commit()

        flash(
            "Candidate added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "candidates.index",
                election_id=election.id
            )
        )

    return render_template(
        "admin/elections/candidates/create.html",
        election=election,
        positions=positions
    )

@candidates_bp.route(
    "/<int:election_id>/candidates/<int:candidate_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit(election_id, candidate_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    candidate = Candidate.query.filter_by(
        id=candidate_id,
        election_id=election.id
    ).first_or_404()

    positions = Position.query.filter_by(
        election_id=election.id
    ).order_by(
        Position.display_order.asc(),
        Position.id.asc()
    ).all()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        position_id = request.form.get(
            "position_id",
            ""
        ).strip()

        manifesto = request.form.get(
            "manifesto",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "active"
        ).strip()

        if not name:

            flash(
                "Candidate name is required.",
                "danger"
            )

            return render_template(
                "admin/elections/candidates/edit.html",
                election=election,
                candidate=candidate,
                positions=positions
            )

        try:

            position_id = int(position_id)

        except ValueError:

            flash(
                "Please select a valid position.",
                "danger"
            )

            return render_template(
                "admin/elections/candidates/edit.html",
                election=election,
                candidate=candidate,
                positions=positions
            )

        position = Position.query.filter_by(
            id=position_id,
            election_id=election.id
        ).first()

        if not position:

            flash(
                "The selected position is invalid.",
                "danger"
            )

            return render_template(
                "admin/elections/candidates/edit.html",
                election=election,
                candidate=candidate,
                positions=positions
            )

        if status not in ["active", "inactive"]:
            status = "active"

        candidate.name = name
        candidate.position_id = position.id
        candidate.manifesto = manifesto or None
        candidate.status = status

        # Replace photo if a new one was uploaded
        photo = request.files.get("photo")

        if photo and photo.filename:

            filename = secure_filename(
                photo.filename
            )

            upload_folder = os.path.join(
                "static",
                "uploads",
                "candidates"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            # Remove old photo
            if candidate.photo:

                old_photo = os.path.join(
                    upload_folder,
                    candidate.photo
                )

                if os.path.exists(old_photo):

                    os.remove(old_photo)

            candidate.photo = filename

            photo.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

        db.session.commit()

        flash(
            "Candidate updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "candidates.index",
                election_id=election.id
            )
        )

    return render_template(
        "admin/elections/candidates/edit.html",
        election=election,
        candidate=candidate,
        positions=positions
    )


@candidates_bp.route(
    "/<int:election_id>/candidates/<int:candidate_id>/delete",
    methods=["POST"]
)
@login_required
def delete(election_id, candidate_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    candidate = Candidate.query.filter_by(
        id=candidate_id,
        election_id=election.id
    ).first_or_404()

    try:

        # Remove candidate photo
        if candidate.photo:

            photo_path = os.path.join(
                "static",
                "uploads",
                "candidates",
                candidate.photo
            )

            if os.path.exists(photo_path):
                os.remove(photo_path)

        db.session.delete(candidate)

        db.session.commit()

        flash(
            "Candidate deleted successfully.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Candidate could not be deleted.",
            "danger"
        )

    return redirect(
        url_for(
            "candidates.index",
            election_id=election.id
        )
    )


@candidates_bp.route(
    "/<int:election_id>/candidates/<int:candidate_id>/toggle-status",
    methods=["POST"]
)
@login_required
def toggle_status(election_id, candidate_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    candidate = Candidate.query.filter_by(
        id=candidate_id,
        election_id=election.id
    ).first_or_404()

    if candidate.status == "active":
        candidate.status = "inactive"
        message = "Candidate deactivated successfully."
    else:
        candidate.status = "active"
        message = "Candidate activated successfully."

    db.session.commit()

    flash(
        message,
        "success"
    )

    return redirect(
        url_for(
            "candidates.index",
            election_id=election.id
        )
    )