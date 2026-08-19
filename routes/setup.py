from flask import Blueprint, render_template, redirect, url_for, flash, request

from extensions import db
from models import Institution, User


setup_bp = Blueprint(
    "setup",
    __name__,
    url_prefix="/setup"
)


@setup_bp.route("/", methods=["GET", "POST"])
def setup():
    # Setup is only available when no administrator exists.
    if User.query.first():
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        institution_name = request.form.get(
            "institution_name", ""
        ).strip()

        institution_code = request.form.get(
            "institution_code", ""
        ).strip().upper()

        institution_email = request.form.get(
            "institution_email", ""
        ).strip().lower()

        institution_phone = request.form.get(
            "institution_phone", ""
        ).strip()

        institution_address = request.form.get(
            "institution_address", ""
        ).strip()

        primary_color = request.form.get(
            "primary_color", "#0d6efd"
        ).strip()

        secondary_color = request.form.get(
            "secondary_color", "#ffffff"
        ).strip()

        admin_name = request.form.get(
            "admin_name", ""
        ).strip()

        admin_email = request.form.get(
            "admin_email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        confirm_password = request.form.get(
            "confirm_password", ""
        )

        # Basic validation
        if not institution_name:
            flash("Institution name is required.", "danger")
            return render_template("setup/setup.html")

        if not institution_code:
            flash("Institution code is required.", "danger")
            return render_template("setup/setup.html")

        if not admin_name:
            flash("Administrator name is required.", "danger")
            return render_template("setup/setup.html")

        if not admin_email:
            flash("Administrator email is required.", "danger")
            return render_template("setup/setup.html")

        if len(password) < 8:
            flash(
                "Administrator password must be at least 8 characters.",
                "danger"
            )
            return render_template("setup/setup.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("setup/setup.html")

        # Check unique institution code
        existing_institution = Institution.query.filter_by(
            code=institution_code
        ).first()

        if existing_institution:
            flash(
                "That institution code already exists.",
                "danger"
            )
            return render_template("setup/setup.html")

        # Check unique administrator email
        existing_user = User.query.filter_by(
            email=admin_email
        ).first()

        if existing_user:
            flash(
                "That administrator email is already registered.",
                "danger"
            )
            return render_template("setup/setup.html")

        try:
            institution = Institution(
                name=institution_name,
                code=institution_code,
                email=institution_email or None,
                phone=institution_phone or None,
                address=institution_address or None,
                primary_color=primary_color or "#0d6efd",
                secondary_color=secondary_color or "#ffffff",
            )

            db.session.add(institution)
            db.session.flush()

            administrator = User(
                institution_id=institution.id,
                name=admin_name,
                email=admin_email,
                role="admin",
                status="active",
            )

            administrator.set_password(password)

            db.session.add(administrator)

            db.session.commit()

            flash(
                "System setup completed successfully. "
                "You can now log in.",
                "success"
            )

            return redirect(url_for("auth.login"))

        except Exception:
            db.session.rollback()

            flash(
                "Setup could not be completed. "
                "Please try again.",
                "danger"
            )

    return render_template("setup/setup.html")