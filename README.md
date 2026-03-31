# Slack Standup Bot

A Flask application that integrates with Slack to automate daily standup meetings. The bot sends a scheduled daily message to a Slack channel, allowing team members to submit their standup responses via an interactive modal.

## Features

- **Scheduled Daily Standups** — Automatically posts a standup prompt to your channel at a configurable time each day.
- **Interactive Modal** — Team members click a button and fill out a clean modal form with three fields: Yesterday, Today, and Blockers.
- **Persistent Storage** — All responses are stored in a SQLite database with clearly defined tables and relationships.
- **Response Tracking** — View standup history per user, per day, or across the whole team.
- **Admin Dashboard** — A simple web view to inspect standup responses.

## Architecture

```
slack-standup-bot/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # SQLAlchemy models (User, StandupResponse)
│   ├── slack_bot.py         # Slack event handlers & modal logic
│   ├── scheduler.py         # APScheduler daily message job
│   ├── routes.py            # Web dashboard routes
│   └── templates/
│       └── dashboard.html   # Admin dashboard template
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── .env.example             # Environment variable template
└── README.md
```

## Database Schema

### `users` table
| Column          | Type     | Description                    |
|-----------------|----------|--------------------------------|
| id              | Integer  | Primary key                    |
| slack_user_id   | String   | Unique Slack user ID           |
| slack_username  | String   | Slack display name             |
| created_at      | DateTime | When the user was first seen   |

### `standup_responses` table
| Column          | Type     | Description                          |
|-----------------|----------|--------------------------------------|
| id              | Integer  | Primary key                          |
| user_id         | Integer  | Foreign key → users.id               |
| yesterday       | Text     | What the user did yesterday          |
| today           | Text     | What the user plans to do today      |
| blockers        | Text     | Any blockers the user is facing      |
| submitted_at    | DateTime | Timestamp of submission              |
| standup_date    | Date     | The date this standup is for         |

## Prerequisites

- Python 3.9+
- A Slack workspace where you can install apps
- A Slack App with the required permissions

## Slack App Setup

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click **Create New App** → **From scratch**.

2. **OAuth & Permissions** — Add these Bot Token Scopes:
   - `chat:write` — Send messages
   - `channels:read` — Read channel info
   - `users:read` — Read user info
   - `commands` — Slash commands (optional)

3. **Interactivity & Shortcuts** — Enable interactivity and set the Request URL to:
   ```
   https://your-domain.com/slack/events
   ```

4. **Event Subscriptions** — Enable events and set the Request URL to:
   ```
   https://your-domain.com/slack/events
   ```
   Subscribe to bot events: `message.channels`

5. **Install the app** to your workspace and copy the Bot User OAuth Token.

6. Invite the bot to your standup channel: `/invite @YourBotName`

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/slack-standup-bot.git
   cd slack-standup-bot
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your Slack credentials
   ```

5. **Run the application:**
   ```bash
   python run.py
   ```

   The app will start on `http://localhost:5000`.

## Configuration

All configuration is done via environment variables (see `.env.example`):

| Variable              | Description                              | Default          |
|-----------------------|------------------------------------------|------------------|
| `SLACK_BOT_TOKEN`     | Bot User OAuth Token (xoxb-...)          | *required*       |
| `SLACK_SIGNING_SECRET`| Slack app signing secret                 | *required*       |
| `SLACK_CHANNEL_ID`    | Channel ID to post standups in           | *required*       |
| `STANDUP_HOUR`        | Hour to send standup prompt (24h format) | `9`              |
| `STANDUP_MINUTE`      | Minute to send standup prompt            | `0`              |
| `TIMEZONE`            | Timezone for scheduling                  | `America/New_York` |
| `DATABASE_URL`        | Database connection string               | `sqlite:///standup.db` |
| `FLASK_SECRET_KEY`    | Flask secret key                         | auto-generated   |

## Usage

### For Team Members
1. The bot posts a standup prompt in the configured channel each morning.
2. Click the **"Submit Standup"** button.
3. Fill out the modal with your yesterday, today, and blockers.
4. Click **Submit** — your response is saved and a confirmation appears.

### For Admins
- Visit `http://localhost:5000/dashboard` to view all standup responses.
- Query the SQLite database directly to inspect data:
  ```bash
  sqlite3 instance/standup.db
  ```
  ```sql
  SELECT u.slack_username, s.yesterday, s.today, s.blockers, s.standup_date
  FROM standup_responses s
  JOIN users u ON s.user_id = u.id
  ORDER BY s.submitted_at DESC;
  ```

### Manual Trigger
- Visit `http://localhost:5000/trigger-standup` to manually send the standup prompt (useful for testing).

## Development

### Running with ngrok (for local Slack development)
```bash
ngrok http 5000
```
Then update your Slack app's Interactivity and Event Subscription URLs with the ngrok URL.

## License

MIT
