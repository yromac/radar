"""Event listing and calendar feed routes."""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import or_

from db.models import get_db, Event, EventCategory, EventSource
from api.schemas import EventOut, SyncResult
from calendar_push.ical import events_to_ical

router = APIRouter(prefix="/events", tags=["events"])


def _apply_filters(
    query,
    category: Optional[str],
    source: Optional[str],
    is_free: Optional[bool],
    is_exclusive: Optional[bool],
    start_after: Optional[datetime],
    start_before: Optional[datetime],
    search: Optional[str],
):
    if category:
        try:
            query = query.filter(Event.category == EventCategory(category))
        except ValueError:
            pass
    if source:
        try:
            query = query.filter(Event.source == EventSource(source))
        except ValueError:
            pass
    if is_free is not None:
        query = query.filter(Event.is_free == is_free)
    if is_exclusive is not None:
        query = query.filter(Event.is_exclusive == is_exclusive)
    if start_after:
        query = query.filter(Event.start_dt >= start_after)
    if start_before:
        query = query.filter(Event.start_dt <= start_before)
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(Event.title.ilike(term), Event.description.ilike(term))
        )
    return query


@router.get("/", response_model=list[EventOut])
def list_events(
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    is_free: Optional[bool] = Query(None),
    is_exclusive: Optional[bool] = Query(None),
    start_after: Optional[datetime] = Query(None),
    start_before: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """List upcoming events with optional filters."""
    query = db.query(Event).order_by(Event.start_dt.asc())
    query = _apply_filters(
        query, category, source, is_free, is_exclusive, start_after, start_before, search
    )
    events = query.offset(offset).limit(limit).all()
    return events


@router.get("/feed.ics")
def ical_feed(
    category: Optional[str] = Query(None),
    is_free: Optional[bool] = Query(None),
    is_exclusive: Optional[bool] = Query(None),
    start_after: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Download or subscribe to an iCal (.ics) feed of events.

    Subscribe this URL in Apple Calendar, Google Calendar, or Outlook to get
    Radar events pushed to your calendar automatically.
    """
    query = db.query(Event).order_by(Event.start_dt.asc())
    query = _apply_filters(
        query, category, None, is_free, is_exclusive, start_after, None, search
    )
    events = query.limit(500).all()
    ical_bytes = events_to_ical(events)
    return Response(
        content=ical_bytes,
        media_type="text/calendar",
        headers={"Content-Disposition": 'attachment; filename="radar-events.ics"'},
    )


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
