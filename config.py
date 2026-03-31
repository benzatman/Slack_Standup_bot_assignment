import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    # Flask
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", os.urandom(32).hex())

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///standup.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Slack
    SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
    SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

    # Scheduling
    STANDUP_HOUR = int(os.environ.get("STANDUP_HOUR", 9))
    STANDUP_MINUTE = int(os.environ.get("STANDUP_MINUTE", 0))
    TIMEZONE = os.environ.get("TIMEZONE", "America/New_York")
