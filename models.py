from datetime import date, datetime, timezone

from app import db


class User(db.Model):
    """Represents a Slack workspace member who has submitted a standup."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    slack_user_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    slack_username = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationship: one user has many standup responses
    responses = db.relationship(
        "StandupResponse", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.slack_username} ({self.slack_user_id})>"


class StandupResponse(db.Model):
    """A single standup submission from a user for a given date."""

    __tablename__ = "standup_responses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    yesterday = db.Column(db.Text, nullable=False)
    today = db.Column(db.Text, nullable=False)
    blockers = db.Column(db.Text, nullable=False, default="None")
    submitted_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    standup_date = db.Column(db.Date, nullable=False, default=date.today, index=True)

    # Composite unique constraint: one response per user per day
    __table_args__ = (
        db.UniqueConstraint("user_id", "standup_date", name="uq_user_standup_date"),
    )

    def __repr__(self):
        return f"<StandupResponse user_id={self.user_id} date={self.standup_date}>"

    def to_dict(self):
        """Serialize the response for display or API use."""
        return {
            "id": self.id,
            "user": self.user.slack_username,
            "yesterday": self.yesterday,
            "today": self.today,
            "blockers": self.blockers,
            "submitted_at": self.submitted_at.isoformat(),
            "standup_date": self.standup_date.isoformat(),
        }
