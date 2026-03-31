from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    """Flask application factory."""
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Initialize database
    db.init_app(app)

    with app.app_context():
        # Import models so tables are registered before create_all
        from app import models  # noqa: F401

        db.create_all()

        # Register web routes (dashboard, manual trigger)
        from app.routes import bp as routes_bp

        app.register_blueprint(routes_bp)

        # Initialize the Slack bot handlers
        from app.slack_bot import init_slack_bot

        init_slack_bot(app)

        # Start the scheduler for daily standup prompts
        from app.scheduler import start_scheduler

        start_scheduler(app)

    return app
