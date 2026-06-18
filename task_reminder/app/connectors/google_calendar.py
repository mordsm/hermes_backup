from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import settings
from .base import Connector, ExternalItem


SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarConnector(Connector):
    source_name = "google_calendar"

    def _token_path(self) -> Path | None:
        if not settings.google_token_file:
            return None
        return Path(settings.google_token_file)

    def _client_secret_path(self) -> Path | None:
        if not settings.google_client_secret_file:
            return None
        return Path(settings.google_client_secret_file)

    def authorize(self) -> Credentials | None:
        secret_path = self._client_secret_path()
        token_path = self._token_path()
        if secret_path is None or token_path is None:
            return None
        if not secret_path.exists():
            return None

        flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
        creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    def _credentials(self) -> Credentials | None:
        token_path = self._token_path()
        if token_path is None or not token_path.exists():
            return None

        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        if creds.valid:
            return creds
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            token_path.write_text(creds.to_json(), encoding="utf-8")
            return creds
        return None

    def _service(self):
        creds = self._credentials()
        if creds is None:
            return None
        return build("calendar", "v3", credentials=creds, cache_discovery=False)

    def _event_datetime(self, payload: dict) -> datetime | None:
        value = payload.get("dateTime") or payload.get("date")
        if not value:
            return None
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(ZoneInfo(settings.app_timezone))

    def sync(self) -> list[ExternalItem]:
        service = self._service()
        if service is None:
            return []

        now = datetime.now(tz=ZoneInfo(settings.app_timezone))
        window_end = now + timedelta(days=30)
        response = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=window_end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                maxResults=250,
            )
            .execute()
        )
        items: list[ExternalItem] = []
        for event in response.get("items", []):
            start = self._event_datetime(event.get("start", {}))
            end = self._event_datetime(event.get("end", {}))
            items.append(
                ExternalItem(
                    source=self.source_name,
                    source_object_id=event["id"],
                    title=event.get("summary") or "Untitled event",
                    description=event.get("description"),
                    due_at=start,
                    deadline_at=end,
                    source_url=event.get("htmlLink"),
                    raw=event,
                )
            )
        return items

    def mark_done(self, source_object_id: str) -> None:
        return None
