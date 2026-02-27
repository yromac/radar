from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Float,
    ForeignKey, Enum, create_engine, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.sql import func
import enum
import uuid

from config import settings


class Base(DeclarativeBase):
    pass


class EventSource(str, enum.Enum):
    LUMA = "luma"
    PHILLY_FILM_FESTIVAL = "philly_film_festival"
    MUSEUM = "museum"
    BEST_OF_CITY = "best_of_city"
    PARTNER = "partner"


class EventCategory(str, enum.Enum):
    ARTS = "arts"
    FILM = "film"
    MUSIC = "music"
    FOOD = "food"
    SPORTS = "sports"
    TECH = "tech"
    COMMUNITY = "community"
    OUTDOOR = "outdoor"
    WELLNESS = "wellness"
    OTHER = "other"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_event_source"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String)
    image_url = Column(String)

    start_dt = Column(DateTime(timezone=True), nullable=False)
    end_dt = Column(DateTime(timezone=True))
    all_day = Column(Boolean, default=False)

    venue_name = Column(String)
    venue_address = Column(String)
    lat = Column(Float)
    lng = Column(Float)

    source = Column(Enum(EventSource), nullable=False)
    source_id = Column(String)  # original ID from the scraped platform

    category = Column(Enum(EventCategory), default=EventCategory.OTHER)
    tags = Column(Text)  # comma-separated

    is_free = Column(Boolean)
    price_min = Column(Float)
    price_max = Column(Float)

    is_exclusive = Column(Boolean, default=False)  # partner exclusive events

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    partner_id = Column(String, ForeignKey("partners.id"), nullable=True)
    partner = relationship("Partner", back_populates="events")


class Partner(Base):
    __tablename__ = "partners"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    business_name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False, unique=True)
    website = Column(String)
    description = Column(Text)
    category = Column(Enum(EventCategory))
    api_key = Column(String, unique=True)  # key issued to the partner
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    events = relationship("Event", back_populates="partner")


# DB session factory
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
