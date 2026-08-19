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
from models import Election, Position


positions_bp = Blueprint(
    "positions",
    __name__,
    url_prefix="/admin/elections"
)


@positions_bp.route("/<int:election_id>/positions")
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

    return render_template(
        "admin/elections/positions/index.html",
        election=election,
        positions=positions
    )


@positions_bp.route(
    "/<int:election_id>/positions/create",
    methods=["GET", "POST"]
)
@login_required
def create(election_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        display_order = request.form.get(
            "display_order",
            "1"
        ).strip()

        max_selections = request.form.get(
            "max_selections",
            "1"
        ).strip()

        if not name:

            flash(
                "Position name is required.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/create.html",
                election=election
            )

        try:

            display_order = int(display_order)

            max_selections = int(max_selections)

        except ValueError:

            flash(
                "Display order and maximum selections must be numbers.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/create.html",
                election=election
            )

        if display_order < 1:

            flash(
                "Display order must be at least 1.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/create.html",
                election=election
            )

        if max_selections < 1:

            flash(
                "Maximum selections must be at least 1.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/create.html",
                election=election
            )

        position = Position(
            election_id=election.id,
            name=name,
            description=description or None,
            display_order=display_order,
            max_selections=max_selections
        )

        db.session.add(position)
        db.session.commit()

        flash(
            "Position created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "positions.index",
                election_id=election.id
            )
        )

    return render_template(
        "admin/elections/positions/create.html",
        election=election
    )


@positions_bp.route(
    "/<int:election_id>/positions/<int:position_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit(election_id, position_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    position = Position.query.filter_by(
        id=position_id,
        election_id=election.id
    ).first_or_404()

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        display_order = request.form.get(
            "display_order",
            "1"
        ).strip()

        max_selections = request.form.get(
            "max_selections",
            "1"
        ).strip()

        if not name:

            flash(
                "Position name is required.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/edit.html",
                election=election,
                position=position
            )

        try:

            display_order = int(display_order)

            max_selections = int(max_selections)

        except ValueError:

            flash(
                "Display order and maximum selections must be numbers.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/edit.html",
                election=election,
                position=position
            )

        if display_order < 1:

            flash(
                "Display order must be at least 1.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/edit.html",
                election=election,
                position=position
            )

        if max_selections < 1:

            flash(
                "Maximum selections must be at least 1.",
                "danger"
            )

            return render_template(
                "admin/elections/positions/edit.html",
                election=election,
                position=position
            )

        position.name = name

        position.description = (
            description or None
        )

        position.display_order = display_order

        position.max_selections = max_selections

        db.session.commit()

        flash(
            "Position updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "positions.index",
                election_id=election.id
            )
        )

    return render_template(
        "admin/elections/positions/edit.html",
        election=election,
        position=position
    )


@positions_bp.route(
    "/<int:election_id>/positions/<int:position_id>/delete",
    methods=["POST"]
)
@login_required
def delete(election_id, position_id):

    election = Election.query.filter_by(
        id=election_id,
        institution_id=current_user.institution_id
    ).first_or_404()

    position = Position.query.filter_by(
        id=position_id,
        election_id=election.id
    ).first_or_404()

    db.session.delete(position)

    db.session.commit()

    flash(
        "Position deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "positions.index",
            election_id=election.id
        )
    )