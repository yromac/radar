"""
Event recommendation engine.

Scores upcoming events against a user's learned profile and returns the
top N events to push, ensuring category diversity.
"""
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from db.models import Event, EventPush, User, UserProfile

# Default number of events to push per cycle
PUSH_COUNT = 2

# Small random bonus added to every score so new users get varied picks
# and users don't get permanently locked into one category.
DISCOVERY_NOISE = 1.0


def _score_event(event: Event, profile: Optional[UserProfile]) -> float:
    """
    Score one event for a user.

    Higher score → more likely to be selected.
    When there is no profile yet every event gets a random score, which
    gives a good cold-start spread across categories.
    """
    if profile is None:
        return random.random() * DISCOVERY_NOISE

    score = 0.0

    # ── Category interest ──────────────────────────────────────────────
    weights: dict = profile.category_weights or {}
    cat_key = event.category.value if event.category else "other"
    score += weights.get(cat_key, 0.0) * 2.0

    # ── Time-of-week / time-of-day preference ─────────────────────────
    if event.start_dt:
        dt = event.start_dt
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        is_weekend = dt.weekday() >= 5          # Sat / Sun
        is_evening = 17 <= dt.hour <= 22        # 5 PM – 10 PM

        score += (profile.prefers_weekends or 0.0) * (1.0 if is_weekend else -0.3)
        score += (profile.prefers_evenings or 0.0) * (1.0 if is_evening else -0.3)

    # ── Price preference ───────────────────────────────────────────────
    if event.is_free is True:
        score += (profile.free_preference or 0.0) * 0.5
    elif event.is_free is False:
        score -= (profile.free_preference or 0.0) * 0.5

    # ── Small boost for partner-exclusive events ───────────────────────
    if event.is_exclusive:
        score += 0.3

    # ── Discovery noise so the algorithm never fully converges ─────────
    score += random.uniform(0, DISCOVERY_NOISE)

    return score


def pick_events_for_user(db: Session, user: User, n: int = PUSH_COUNT) -> list[Event]:
    """
    Return up to *n* upcoming events best suited to *user*.

    Already-pushed events are excluded.  We try to return events from
    distinct categories so the user gets variety even early on.
    """
    now = datetime.now(tz=timezone.utc)

    already_pushed_ids = (
        db.query(EventPush.event_id)
        .filter(EventPush.user_id == user.id)
        .subquery()
    )

    upcoming: list[Event] = (
        db.query(Event)
        .filter(
            Event.start_dt > now,
            ~Event.id.in_(already_pushed_ids),
        )
        .all()
    )

    if not upcoming:
        return []

    profile = user.profile
    scored = sorted(upcoming, key=lambda e: _score_event(e, profile), reverse=True)

    # Select with category diversity: prefer one event per category
    selected: list[Event] = []
    used_categories: set[str] = set()

    for event in scored:
        cat = event.category.value if event.category else "other"
        if cat not in used_categories:
            selected.append(event)
            used_categories.add(cat)
            if len(selected) >= n:
                break

    # If we couldn't fill *n* slots from distinct categories, fill from top scores
    for event in scored:
        if len(selected) >= n:
            break
        if event not in selected:
            selected.append(event)

    return selected[:n]
