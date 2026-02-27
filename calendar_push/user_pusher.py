"""
Per-user Google Calendar pusher.

Extends the single-user GoogleCalendarPusher to support multiple users,
each with their own stored OAuth token.  Every pushed event includes
yes / maybe / no response links in the description so Radar can learn
what the user likes.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from db.models import Event, EventPush, User
from calendar_push.google_calendar import SCOPES, _get_or_create_calendar
from config import settings

logger = logging.getLogger(__name__)


def _build_response_description(event: Event, push_id: str) -> str:
    """Event description that includes clickable yes / maybe / no links."""
    base = settings.app_base_url.rstrip("/")
    parts = []

    if event.is_exclusive:
        parts.append("★ EXCLUSIVE — Radar Partner Event")

    if event.description:
        parts.append(event.description[:1500])

    if event.is_free is True:
        parts.append("FREE")
    elif event.price_min is not None:
        price = f"From ${event.price_min:.0f}"
        if event.price_max and event.price_max != event.price_min:
            price += f" – ${event.price_max:.0f}"
        parts.append(price)

    if event.url:
        parts.append(f"More info: {event.url}")

    parts.append(
        f"--- Tell Radar what you think ---\n"
        f"Going       -> {base}/users/respond/{push_id}/yes\n"
        f"Maybe       -> {base}/users/respond/{push_id}/maybe\n"
        f"Not for me  -> {base}/users/respond/{push_id}/no"
    )

    return "\n\n".join(parts)


def _build_gcal_body(event: Event, push_id: str) -> dict:
    """Convert a Radar Event to a Google Calendar event body with response links."""
    start_dt = event.start_dt
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)

    body: dict = {
        "summary": event.title,
        "description": _build_response_description(event, push_id),
        "source": {"title": "Radar", "url": event.url or ""},
        "extendedProperties": {
            "private": {
                "radar_event_id": event.id,
                "radar_push_id": push_id,
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
        body["start"] = {"dateTime": start_dt.isoformat(), "timeZone": settings.timezone}
        if event.end_dt:
            end_dt = event.end_dt
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=timezone.utc)
            body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": settings.timezone}
        else:
            body["end"] = {
                "dateTime": (start_dt + timedelta(hours=2)).isoformat(),
                "timeZone": settings.timezone,
            }

    if event.venue_name or event.venue_address:
        body["location"] = ", ".join(filter(None, [event.venue_name, event.venue_address]))

    return body


class UserCalendarPusher:
    """Pushes events to a specific user's Google Calendar and records EventPush rows."""

    def __init__(self, user: User):
        self._user = user
        self._service = None
        self._calendar_id: Optional[str] = None

    def _connect(self, db: Session) -> None:
        """Build Google API service from the user's stored token, refreshing if needed."""
        if not self._user.google_token_json:
            raise ValueError(f"User {self._user.id} has no stored Google token")

        token_data = json.loads(self._user.google_token_json)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Persist the refreshed token
            self._user.google_token_json = creds.to_json()
            db.add(self._user)
            db.flush()

        self._service = build("calendar", "v3", credentials=creds)

        if self._user.google_calendar_id:
            self._calendar_id = self._user.google_calendar_id
        else:
            self._calendar_id = _get_or_create_calendar(self._service)
            self._user.google_calendar_id = self._calendar_id
            db.add(self._user)
            db.flush()

    def push_events(self, db: Session, events: list[Event]) -> list[EventPush]:
        """
        Push *events* to the user's Radar calendar.

        Creates an EventPush record for each event (before the calendar call
        so we can embed the push ID in the description), then stores the
        Google Calendar event ID on success.

        Returns the list of successfully-pushed EventPush records.
        """
        self._connect(db)

        pushes: list[EventPush] = []
        for event in events:
            # Create the DB record first to obtain its ID
            push = EventPush(
                user_id=self._user.id,
                event_id=event.id,
                pushed_at=datetime.now(tz=timezone.utc),
            )
            db.add(push)
            db.flush()  # assigns push.id

            body = _build_gcal_body(event, push.id)
            try:
                result = self._service.events().insert(
                    calendarId=self._calendar_id, body=body
                ).execute()
                push.gcal_event_id = result["id"]
                logger.info(f"[user_pusher] pushed '{event.title}' → {self._user.email}")
                pushes.append(push)
            except HttpError as exc:
                logger.error(f"[user_pusher] failed '{event.title}': {exc}")
                db.delete(push)

        db.commit()
        return pushes
