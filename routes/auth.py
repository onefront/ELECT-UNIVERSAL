from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from services.audit_service import log_activity
from models.user import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not User.query.first():
        return redirect(url_for("setup.setup"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.status == "active" and user.check_password(password):
            login_user(user)
            log_activity(
                action="LOGIN",
                description=f"Administrator {user.name} logged into the system.",
                entity_type="User",
                entity_id=user.id
            )
            return redirect(url_for("admin.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():

    log_activity(
        action="LOGOUT",
        description=f"Administrator {current_user.name} logged out of the system.",
        entity_type="User",
        entity_id=current_user.id
    )

    logout_user()

    return redirect(url_for("auth.login"))