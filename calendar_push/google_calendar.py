"""Google Calendar integration.

Pushes Radar events to a user's Google Calendar using OAuth2.
Requires credentials.json from Google Cloud Console
(OAuth 2.0 Client ID for a desktop application).
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import os

from db.models import Event
from config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
RADAR_CALENDAR_NAME = "Radar — Philadelphia Events"


def _get_credentials() -> Credentials:
    """Load or refresh OAuth2 credentials."""
    creds: Optional[Credentials] = None
    token_file = settings.google_token_file

    if token_file and os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not settings.google_credentials_file or not os.path.exists(
                settings.google_credentials_file
            ):
                raise FileNotFoundError(
                    "Google credentials file not found. "
                    "Download credentials.json from Google Cloud Console and set "
                    "GOOGLE_CREDENTIALS_FILE in your .env file."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.google_credentials_file, SCOPES
            )
            creds = flow.run_local_server(port=0)

        if token_file:
            with open(token_file, "w") as f:
                f.write(creds.to_json())

    return creds


def _get_or_create_calendar(service) -> str:
    """Return the Radar calendar ID, creating it if it doesn't exist."""
    calendars = service.calendarList().list().execute()
    for cal in calendars.get("items", []):
        if cal.get("summary") == RADAR_CALENDAR_NAME:
            return cal["id"]

    new_cal = service.calendars().insert(body={
        "summary": RADAR_CALENDAR_NAME,
        "description": "Events curated by Radar — Philadelphia's antidote to mundane days.",
        "timeZone": settings.timezone,
    }).execute()
    logger.info(f"[google_calendar] created calendar: {new_cal['id']}")
    return new_cal["id"]


def _event_to_gcal_body(event: Event) -> dict:
    """Convert a Radar DB Event to a Google Calendar event body."""
    start_dt: datetime = event.start_dt
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)

    body: dict = {
        "summary": event.title,
        "description": _build_description(event),
        "source": {"title": "Radar", "url": event.url or ""},
        "extendedProperties": {
            "private": {
                "radar_id": event.id,
                "radar_source": event.source.value if event.source else "",
            }
        },
    }

    if event.all_day:
        body["start"] = {"date": start_dt.date().isoformat()}
        end = event.end_dt or start_dt
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
        body["end"] = {"date": end.date().isoformat()}
    else:
        body["start"] = {
            "dateTime": start_dt.isoformat(),
            "timeZone": settings.timezone,
        }
        if event.end_dt:
            end_dt = event.end_dt
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": settings.timezone}
        else:
            # Default: 2 hours
            from datetime import timedelta
            body["end"] = {
                "dateTime": (start_dt + timedelta(hours=2)).isoformat(),
                "timeZone": settings.timezone,
            }

    if event.venue_name or event.venue_address:
        body["location"] = ", ".join(
            filter(None, [event.venue_name, event.venue_address])
        )

    return body


def _build_description(event: Event) -> str:
    parts = []
    if event.is_exclusive:
        parts.append("★ EXCLUSIVE — Radar Partner Event")
    if event.description:
        parts.append(event.description[:2000])  # GCal has limits
    if event.is_free is True:
        parts.append("FREE")
    elif event.price_min is not None:
        price = f"From ${event.price_min:.0f}"
        if event.price_max and event.price_max != event.price_min:
            price += f" – ${event.price_max:.0f}"
        parts.append(price)
    if event.url:
        parts.append(f"\nMore info: {event.url}")
    return "\n\n".join(parts)


class GoogleCalendarPusher:
    """Pushes/syncs Radar events to Google Calendar."""

    def __init__(self):
        self._service = None
        self._calendar_id = None

    def _connect(self):
        if self._service is None:
            creds = _get_credentials()
            self._service = build("calendar", "v3", credentials=creds)
            self._calendar_id = _get_or_create_calendar(self._service)

    def push_event(self, event: Event) -> Optional[str]:
        """Insert a single event. Returns the Google Calendar event ID."""
        self._connect()
        body = _event_to_gcal_body(event)
        try:
            result = self._service.events().insert(
                calendarId=self._calendar_id, body=body
            ).execute()
            logger.info(f"[google_calendar] pushed: {event.title}")
            return result["id"]
        except HttpError as exc:
            logger.error(f"[google_calendar] push failed for '{event.title}': {exc}")
            return None

    def push_events(self, events: list[Event]) -> dict:
        """Batch-push a list of events. Returns counts."""
        self._connect()
        pushed = failed = 0
        for event in events:
            result = self.push_event(event)
            if result:
                pushed += 1
            else:
                failed += 1
        return {"pushed": pushed, "failed": failed}
