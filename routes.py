from datetime import date, timedelta

from flask import Blueprint, jsonify, render_template, request

from app import db
from app.models import StandupResponse, User

bp = Blueprint("routes", __name__)


@bp.route("/")
def index():
    """Health check / landing page."""
    return jsonify(
        {
            "status": "ok",
            "app": "Slack Standup Bot",
            "endpoints": {
                "dashboard": "/dashboard",
                "trigger": "/trigger-standup",
                "api_responses": "/api/responses",
            },
        }
    )


@bp.route("/dashboard")
def dashboard():
    """Render the admin dashboard showing recent standup responses."""
    # Default to today; allow ?date=YYYY-MM-DD query param
    date_str = request.args.get("date")
    if date_str:
        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    responses = (
        StandupResponse.query.filter_by(standup_date=selected_date)
        .join(User)
        .order_by(StandupResponse.submitted_at.desc())
        .all()
    )

    # Build navigation dates
    prev_date = selected_date - timedelta(days=1)
    next_date = selected_date + timedelta(days=1)

    return render_template(
        "dashboard.html",
        responses=responses,
        selected_date=selected_date,
        prev_date=prev_date,
        next_date=next_date,
        today=date.today(),
    )


@bp.route("/trigger-standup", methods=["GET"])
def trigger_standup():
    """Manually trigger the standup prompt (useful for testing)."""
    from flask import current_app

    from app.slack_bot import send_standup_prompt

    channel_id = current_app.config["SLACK_CHANNEL_ID"]
    if not channel_id:
        return jsonify({"error": "SLACK_CHANNEL_ID not configured"}), 400

    send_standup_prompt(channel_id)
    return jsonify({"status": "Standup prompt sent", "channel": channel_id})


@bp.route("/api/responses")
def api_responses():
    """JSON API to fetch standup responses, filterable by date and user."""
    date_str = request.args.get("date")
    user_id = request.args.get("user_id")

    query = StandupResponse.query.join(User)

    if date_str:
        try:
            query = query.filter(
                StandupResponse.standup_date == date.fromisoformat(date_str)
            )
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    if user_id:
        query = query.filter(User.slack_user_id == user_id)

    responses = query.order_by(StandupResponse.submitted_at.desc()).limit(100).all()

    return jsonify([r.to_dict() for r in responses])
