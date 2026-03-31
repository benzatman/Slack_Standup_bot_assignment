import json
import logging
from datetime import date, datetime, timezone

from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler

from app import db
from app.models import StandupResponse, User

logger = logging.getLogger(__name__)

# Module-level references set during init
slack_app: App = None
handler: SlackRequestHandler = None


def init_slack_bot(flask_app):
    """Initialize the Slack Bolt app and register all handlers."""
    global slack_app, handler

    slack_app = App(
        token=flask_app.config["SLACK_BOT_TOKEN"],
        signing_secret=flask_app.config["SLACK_SIGNING_SECRET"],
    )

    # Store flask_app reference for database access inside handlers
    slack_app._flask_app = flask_app

    _register_handlers(slack_app)

    handler = SlackRequestHandler(slack_app)

    # Register the /slack/events endpoint on the Flask app
    @flask_app.route("/slack/events", methods=["POST"])
    def slack_events():
        return handler.handle(request=__import__("flask").request)

    logger.info("Slack bot initialized and /slack/events route registered.")


def send_standup_prompt(channel_id: str):
    """Post the daily standup prompt with an interactive button to the channel."""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    ":sunrise: *Good morning, team!* :sunrise:\n\n"
                    "It's time for our daily standup. Click the button below "
                    "to share your update for today."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":pencil: Submit Standup",
                        "emoji": True,
                    },
                    "action_id": "open_standup_modal",
                    "style": "primary",
                }
            ],
        },
    ]

    try:
        slack_app.client.chat_postMessage(
            channel=channel_id,
            text="Time for standup! Click the button to submit your update.",
            blocks=blocks,
        )
        logger.info(f"Standup prompt sent to channel {channel_id}")
    except Exception as e:
        logger.error(f"Failed to send standup prompt: {e}")


# ---------------------------------------------------------------------------
# Slack event & interaction handlers
# ---------------------------------------------------------------------------


def _register_handlers(app: App):
    """Register all Slack action and view submission handlers."""

    @app.action("open_standup_modal")
    def handle_open_modal(ack, body, client):
        """When a user clicks 'Submit Standup', open the modal form."""
        ack()

        trigger_id = body["trigger_id"]

        modal_view = {
            "type": "modal",
            "callback_id": "standup_submission",
            "title": {"type": "plain_text", "text": "Daily Standup"},
            "submit": {"type": "plain_text", "text": "Submit"},
            "close": {"type": "plain_text", "text": "Cancel"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "yesterday_block",
                    "label": {
                        "type": "plain_text",
                        "text": "What did you do yesterday?",
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "yesterday_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Describe what you accomplished yesterday...",
                        },
                    },
                },
                {
                    "type": "input",
                    "block_id": "today_block",
                    "label": {
                        "type": "plain_text",
                        "text": "What do you plan to do today?",
                    },
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "today_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Describe your plan for today...",
                        },
                    },
                },
                {
                    "type": "input",
                    "block_id": "blockers_block",
                    "label": {
                        "type": "plain_text",
                        "text": "Any blockers?",
                    },
                    "optional": True,
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "blockers_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "List anything blocking your progress (or leave blank)...",
                        },
                    },
                },
            ],
        }

        try:
            client.views_open(trigger_id=trigger_id, view=modal_view)
        except Exception as e:
            logger.error(f"Failed to open standup modal: {e}")

    @app.view("standup_submission")
    def handle_standup_submission(ack, body, client, view):
        """Process the submitted standup modal and persist the response."""
        ack()

        flask_app = app._flask_app
        values = view["state"]["values"]
        slack_user_id = body["user"]["id"]
        slack_username = body["user"].get("username", "unknown")

        yesterday = values["yesterday_block"]["yesterday_input"]["value"]
        today = values["today_block"]["today_input"]["value"]
        blockers = (
            values["blockers_block"]["blockers_input"]["value"] or "None"
        )

        with flask_app.app_context():
            # Upsert the user record
            user = User.query.filter_by(slack_user_id=slack_user_id).first()
            if not user:
                user = User(
                    slack_user_id=slack_user_id, slack_username=slack_username
                )
                db.session.add(user)
                db.session.flush()  # get user.id before creating response
            else:
                # Keep username in sync
                user.slack_username = slack_username

            # Check if the user already submitted today (update if so)
            today_date = date.today()
            existing = StandupResponse.query.filter_by(
                user_id=user.id, standup_date=today_date
            ).first()

            if existing:
                existing.yesterday = yesterday
                existing.today = today
                existing.blockers = blockers
                existing.submitted_at = datetime.now(timezone.utc)
            else:
                response = StandupResponse(
                    user_id=user.id,
                    yesterday=yesterday,
                    today=today,
                    blockers=blockers,
                    standup_date=today_date,
                )
                db.session.add(response)

            db.session.commit()
            logger.info(
                f"Standup saved for {slack_username} ({slack_user_id}) "
                f"on {today_date}"
            )

        # Send a confirmation DM to the user
        try:
            client.chat_postMessage(
                channel=slack_user_id,
                text=(
                    f":white_check_mark: *Standup recorded for {today_date}!*\n\n"
                    f"*Yesterday:* {yesterday}\n"
                    f"*Today:* {today}\n"
                    f"*Blockers:* {blockers}"
                ),
            )
        except Exception as e:
            logger.error(f"Failed to send confirmation DM to {slack_user_id}: {e}")
