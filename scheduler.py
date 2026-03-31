import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def start_scheduler(flask_app):
    """Start the background scheduler that sends the daily standup prompt."""
    from app.slack_bot import send_standup_prompt

    channel_id = flask_app.config["SLACK_CHANNEL_ID"]
    hour = flask_app.config["STANDUP_HOUR"]
    minute = flask_app.config["STANDUP_MINUTE"]
    tz = flask_app.config["TIMEZONE"]

    if not channel_id:
        logger.warning(
            "SLACK_CHANNEL_ID is not set — scheduler will not send standup prompts."
        )
        return

    def _send_prompt():
        """Wrapper that ensures we run inside the Flask app context."""
        with flask_app.app_context():
            send_standup_prompt(channel_id)

    # Schedule the job: runs Monday–Friday at the configured time
    scheduler.add_job(
        _send_prompt,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=hour,
            minute=minute,
            timezone=tz,
        ),
        id="daily_standup_prompt",
        name="Send daily standup prompt to Slack",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started — standup prompt at {hour:02d}:{minute:02d} ({tz}), "
        f"Mon–Fri, to channel {channel_id}"
    )
