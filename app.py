import os
from flask import Flask, redirect, url_for, send_from_directory
from flask import Flask, render_template
from routes.auth import auth_bp
from routes.elections import elections_bp
from routes.positions import positions_bp
from flask import Flask, redirect, url_for
from routes.admin import admin_bp
from routes.setup import setup_bp
from routes.candidates import candidates_bp
from routes.voters import voters_bp
from routes.voter_auth import voter_auth_bp
from routes.sms import sms_bp
from config import Config
from extensions import db, login_manager, migrate
from models import (
    Institution,
    User,
    Election,
    Position,
    Candidate,
    Voter,
    ElectionVoter,
    Ballot,
    BallotSelection,
    ElectionSettings,
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload directory exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(setup_bp)
    app.register_blueprint(elections_bp)
    app.register_blueprint(positions_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(voters_bp)
    app.register_blueprint(voter_auth_bp)
    app.register_blueprint(sms_bp)






    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            filename
        )

    @app.route("/")
    def index():
        if not User.query.first():
            return redirect(url_for("setup.setup"))

        return render_template(
            "landing.html"
        )

    return app


app = create_app()


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)