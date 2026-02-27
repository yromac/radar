"""iCalendar (.ics) feed generator.

Generates a standards-compliant iCal feed that any calendar app
(Apple Calendar, Outlook, Thunderbird) can subscribe to via URL.
"""
from datetime import datetime, timezone
from typing import Optional

from icalendar import Calendar, Event as ICalEvent, vText, vDatetime
import pytz

from db.models import Event
from config import settings


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=pytz.timezone(settings.timezone))
    return dt


def events_to_ical(events: list[Event], title: str = "Radar — Philadelphia Events") -> bytes:
    """Convert a list of DB events into an iCal binary feed."""
    cal = Calendar()
    cal.add("prodid", "-//Radar//Philadelphia Events//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", title)
    cal.add("x-wr-timezone", settings.timezone)
    cal.add("x-wr-caldesc", "Curated Philadelphia events by Radar.")

    for event in events:
        ical_event = _to_ical_event(event)
        if ical_event:
            cal.add_component(ical_event)

    return cal.to_ical()


def _to_ical_event(event: Event) -> Optional[ICalEvent]:
    try:
        ie = ICalEvent()
        ie.add("uid", f"{event.id}@radar.philly")
        ie.add("summary", event.title)

        start = _aware(event.start_dt)
        ie.add("dtstart", start)

        if event.end_dt:
            ie.add("dtend", _aware(event.end_dt))
        else:
            from datetime import timedelta
            ie.add("dtend", start + timedelta(hours=2))

        if event.description:
            ie.add("description", event.description[:3000])

        if event.url:
            ie.add("url", event.url)

        location_parts = filter(None, [event.venue_name, event.venue_address])
        location = ", ".join(location_parts)
        if location:
            ie.add("location", location)

        if event.lat and event.lng:
            ie.add("geo", (event.lat, event.lng))

        if event.updated_at:
            ie.add("last-modified", _aware(event.updated_at))
        elif event.created_at:
            ie.add("last-modified", _aware(event.created_at))

        categories = []
        if event.category:
            categories.append(event.category.value.upper())
        if event.is_exclusive:
            categories.append("RADAR-EXCLUSIVE")
        if categories:
            ie.add("categories", categories)

        return ie
    except Exception:
        return None
