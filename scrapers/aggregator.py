"""Event aggregator — runs all scrapers, deduplicates, and upserts into the DB."""
import logging
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy.orm import Session

from db.models import Event, EventCategory, EventSource
from .base import RawEvent
from .luma import LumaScraper
from .philly_film_festival import PhillyFilmFestivalScraper
from .museums import ALL_MUSEUM_SCRAPERS
from .best_of_city import VisitPhillyScraper, EventbriteScraper

logger = logging.getLogger(__name__)

ALL_SCRAPERS = [
    LumaScraper(),
    PhillyFilmFestivalScraper(),
    VisitPhillyScraper(),
    EventbriteScraper(),
    *ALL_MUSEUM_SCRAPERS,
]

# If two events share title similarity above this threshold AND overlap in time,
# they are considered duplicates (cross-platform).
DEDUP_TITLE_THRESHOLD = 0.85


def _title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _events_overlap(a: RawEvent, b: RawEvent) -> bool:
    """Return True if the two events happen within 3 hours of each other."""
    delta = abs((a.start_dt - b.start_dt).total_seconds())
    return delta < 3 * 3600


def deduplicate(events: list[RawEvent]) -> list[RawEvent]:
    """Remove near-duplicate events across scrapers.

    Two events are duplicates if:
    - Their titles are very similar (≥ DEDUP_TITLE_THRESHOLD)
    - AND they start within 3 hours of each other

    When a duplicate pair is found, prefer the event with more information
    (longer description, has venue, etc.).
    """
    kept: list[RawEvent] = []
    for candidate in events:
        is_dup = False
        for i, existing in enumerate(kept):
            if _events_overlap(candidate, existing) and \
               _title_similarity(candidate.title, existing.title) >= DEDUP_TITLE_THRESHOLD:
                # Keep the richer record
                if _richness(candidate) > _richness(existing):
                    kept[i] = candidate
                is_dup = True
                break
        if not is_dup:
            kept.append(candidate)
    return kept


def _richness(e: RawEvent) -> int:
    score = 0
    if e.description:
        score += len(e.description)
    if e.venue_name:
        score += 10
    if e.venue_address:
        score += 10
    if e.image_url:
        score += 5
    if e.lat and e.lng:
        score += 5
    return score


def _to_db_event(raw: RawEvent) -> dict:
    """Map a RawEvent to kwargs for db Event model."""
    try:
        source = EventSource(raw.source)
    except ValueError:
        source = EventSource.BEST_OF_CITY

    try:
        category = EventCategory(raw.category)
    except ValueError:
        category = EventCategory.OTHER

    return dict(
        source=source,
        source_id=raw.source_id,
        title=raw.title,
        description=raw.description,
        url=raw.url,
        image_url=raw.image_url,
        start_dt=raw.start_dt,
        end_dt=raw.end_dt,
        all_day=raw.all_day,
        venue_name=raw.venue_name,
        venue_address=raw.venue_address,
        lat=raw.lat,
        lng=raw.lng,
        category=category,
        tags=",".join(raw.tags) if raw.tags else None,
        is_free=raw.is_free,
        price_min=raw.price_min,
        price_max=raw.price_max,
        is_exclusive=False,
    )


def run_all_scrapers() -> list[RawEvent]:
    """Run every registered scraper and return deduplicated events."""
    raw: list[RawEvent] = []
    for scraper in ALL_SCRAPERS:
        raw.extend(scraper.run())
    logger.info(f"[aggregator] total raw events: {len(raw)}")
    unique = deduplicate(raw)
    logger.info(f"[aggregator] after dedup: {len(unique)}")
    return unique


def upsert_events(db: Session, events: list[RawEvent]) -> tuple[int, int]:
    """Insert new events or update existing ones. Returns (created, updated)."""
    created = updated = 0

    for raw in events:
        existing: Optional[Event] = (
            db.query(Event)
            .filter(Event.source == raw.source, Event.source_id == raw.source_id)
            .first()
        )
        kwargs = _to_db_event(raw)

        if existing:
            for k, v in kwargs.items():
                setattr(existing, k, v)
            updated += 1
        else:
            db.add(Event(**kwargs))
            created += 1

    db.commit()
    return created, updated


def sync(db: Session) -> dict:
    """Full pipeline: scrape → dedup → upsert. Returns a summary dict."""
    events = run_all_scrapers()
    created, updated = upsert_events(db, events)
    return {"scraped": len(events), "created": created, "updated": updated}
