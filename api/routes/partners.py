"""Partner business API routes.

Local businesses can register as Radar partners and submit exclusive events
via API key authentication.
"""
import secrets
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from db.models import get_db, Partner, Event, EventSource, EventCategory
from api.schemas import PartnerIn, PartnerOut, PartnerEventIn, EventOut

router = APIRouter(prefix="/partners", tags=["partners"])


def _require_partner(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Partner:
    """Dependency: validates the X-Api-Key header and returns the partner."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Api-Key header",
        )
    partner = db.query(Partner).filter(Partner.api_key == x_api_key, Partner.is_active == True).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or inactive API key",
        )
    return partner


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register_partner(payload: PartnerIn, db: Session = Depends(get_db)):
    """Register a new business as a Radar partner.

    Returns a generated API key — store it securely, it won't be shown again.
    Partners can then submit exclusive events that appear on Radar with a
    special "Exclusive" badge.
    """
    existing = db.query(Partner).filter(Partner.contact_email == payload.contact_email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A partner with this email already exists",
        )
    api_key = secrets.token_urlsafe(32)
    partner = Partner(
        id=str(uuid.uuid4()),
        business_name=payload.business_name,
        contact_email=payload.contact_email,
        website=str(payload.website) if payload.website else None,
        description=payload.description,
        category=EventCategory(payload.category) if payload.category else None,
        api_key=api_key,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)

    return {
        "id": partner.id,
        "business_name": partner.business_name,
        "api_key": api_key,
        "message": (
            "Welcome to Radar! Store your API key securely — it won't be shown again. "
            "Use it in the X-Api-Key header to submit exclusive events."
        ),
    }


@router.get("/me", response_model=PartnerOut)
def get_my_profile(partner: Partner = Depends(_require_partner)):
    """Return the authenticated partner's profile."""
    return partner


@router.post("/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def submit_exclusive_event(
    payload: PartnerEventIn,
    partner: Partner = Depends(_require_partner),
    db: Session = Depends(get_db),
):
    """Submit an exclusive event as a Radar partner.

    These events appear in Radar with an "Exclusive" badge and are included
    in the iCal feed. Great for happy hours, private screenings, pop-ups, etc.
    """
    try:
        category = EventCategory(payload.category) if payload.category else EventCategory.OTHER
    except ValueError:
        category = EventCategory.OTHER

    event = Event(
        id=str(uuid.uuid4()),
        source=EventSource.PARTNER,
        source_id=f"partner-{partner.id}-{uuid.uuid4().hex[:8]}",
        title=payload.title,
        description=payload.description,
        url=str(payload.url) if payload.url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        start_dt=payload.start_dt,
        end_dt=payload.end_dt,
        all_day=payload.all_day,
        venue_name=payload.venue_name,
        venue_address=payload.venue_address,
        lat=payload.lat,
        lng=payload.lng,
        category=category,
        tags=",".join(payload.tags) if payload.tags else None,
        is_free=payload.is_free,
        price_min=payload.price_min,
        price_max=payload.price_max,
        is_exclusive=True,
        partner_id=partner.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/events", response_model=list[EventOut])
def list_my_events(
    partner: Partner = Depends(_require_partner),
    db: Session = Depends(get_db),
):
    """List all events submitted by this partner."""
    return db.query(Event).filter(Event.partner_id == partner.id).order_by(Event.start_dt).all()


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_event(
    event_id: str,
    partner: Partner = Depends(_require_partner),
    db: Session = Depends(get_db),
):
    """Delete one of this partner's events."""
    event = db.query(Event).filter(
        Event.id == event_id, Event.partner_id == partner.id
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    db.delete(event)
    db.commit()
