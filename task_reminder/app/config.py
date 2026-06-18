from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./task_reminder.db")
    app_timezone: str = os.getenv("APP_TIMEZONE", "Asia/Jerusalem")

    telegram_bot_token: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str | None = os.getenv("TELEGRAM_CHAT_ID")

    google_client_secret_file: str | None = os.getenv("GOOGLE_CLIENT_SECRET_FILE")
    google_token_file: str | None = os.getenv("GOOGLE_TOKEN_FILE")

    trello_api_key: str | None = os.getenv("TRELLO_API_KEY")
    trello_token: str | None = os.getenv("TRELLO_TOKEN")
    trello_board_id: str | None = os.getenv("TRELLO_BOARD_ID")
    trello_done_list_id: str | None = os.getenv("TRELLO_DONE_LIST_ID")

    alert_dry_run: bool = os.getenv("ALERT_DRY_RUN", "true").lower() in {"1", "true", "yes", "on"}


settings = Settings()
