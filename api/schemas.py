"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl, EmailStr

from db.models import EventCategory, EventSource


class EventOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    url: Optional[str]
    image_url: Optional[str]
    start_dt: datetime
    end_dt: Optional[datetime]
    all_day: bool
    venue_name: Optional[str]
    venue_address: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    source: EventSource
    category: EventCategory
    tags: Optional[str]
    is_free: Optional[bool]
    price_min: Optional[float]
    price_max: Optional[float]
    is_exclusive: bool

    model_config = {"from_attributes": True}


class EventFilter(BaseModel):
    category: Optional[EventCategory] = None
    source: Optional[EventSource] = None
    is_free: Optional[bool] = None
    is_exclusive: Optional[bool] = None
    start_after: Optional[datetime] = None
    start_before: Optional[datetime] = None
    search: Optional[str] = None  # title / description keyword


class PartnerEventIn(BaseModel):
    """Schema for a business partner submitting an exclusive event."""
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    start_dt: datetime
    end_dt: Optional[datetime] = None
    all_day: bool = False
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    category: EventCategory = EventCategory.OTHER
    tags: Optional[list[str]] = None
    is_free: Optional[bool] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None


class PartnerIn(BaseModel):
    business_name: str
    contact_email: EmailStr
    website: Optional[str] = None
    description: Optional[str] = None
    category: Optional[EventCategory] = None


class PartnerOut(BaseModel):
    id: str
    business_name: str
    contact_email: str
    website: Optional[str]
    description: Optional[str]
    category: Optional[EventCategory]
    is_active: bool

    model_config = {"from_attributes": True}


class SyncResult(BaseModel):
    scraped: int
    created: int
    updated: int


class UserOut(BaseModel):
    id: str
    email: str
    google_calendar_id: Optional[str]
    last_push_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileOut(BaseModel):
    id: str
    user_id: str
    category_weights: dict
    prefers_weekends: float
    prefers_evenings: float
    free_preference: float
    total_yes: int
    total_no: int
    total_maybe: int
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class PushResult(BaseModel):
    pushed: int
    event_ids: list[str]
    message: str
