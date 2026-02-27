"""
User profile updater.

Each time a user responds to a pushed event (yes / maybe / no) we nudge
their interest weights in the right direction.  All weights are clamped to
[-WEIGHT_CLAMP, +WEIGHT_CLAMP] to prevent runaway values.
"""
from datetime import datetime, timezone

from db.models import Event, UserProfile

# How much each response type moves each dimension
SIGNALS: dict[str, dict[str, float]] = {
    "yes":   {"category": 2.0,  "time": 1.0,  "price": 0.8},
    "maybe": {"category": 0.5,  "time": 0.2,  "price": 0.1},
    "no":    {"category": -1.0, "time": -0.4, "price": -0.3},
}

WEIGHT_CLAMP = 10.0


def _clamp(value: float) -> float:
    return max(-WEIGHT_CLAMP, min(WEIGHT_CLAMP, value))


def update_profile(profile: UserProfile, event: Event, response: str) -> None:
    """
    Mutate *profile* in place based on *response* to *event*.

    The caller is responsible for committing the session.
    """
    signals = SIGNALS.get(response)
    if not signals:
        return

    cat_delta   = signals["category"]
    time_delta  = signals["time"]
    price_delta = signals["price"]

    # ── 1. Category weight ────────────────────────────────────────────
    weights: dict = dict(profile.category_weights or {})
    cat_key = event.category.value if event.category else "other"
    weights[cat_key] = _clamp(weights.get(cat_key, 0.0) + cat_delta)
    profile.category_weights = weights  # reassign so SQLAlchemy detects the change

    # ── 2. Time-of-week / time-of-day preference ──────────────────────
    if event.start_dt:
        dt = event.start_dt
        if dt.tzinfo is None:
            from datetime import timezone as tz
            dt = dt.replace(tzinfo=tz.utc)

        is_weekend = dt.weekday() >= 5
        is_evening = 17 <= dt.hour <= 22

        profile.prefers_weekends = _clamp(
            (profile.prefers_weekends or 0.0) + time_delta * (1.0 if is_weekend else -1.0)
        )
        profile.prefers_evenings = _clamp(
            (profile.prefers_evenings or 0.0) + time_delta * (1.0 if is_evening else -1.0)
        )

    # ── 3. Price sensitivity ──────────────────────────────────────────
    if event.is_free is True:
        profile.free_preference = _clamp((profile.free_preference or 0.0) + price_delta)
    elif event.is_free is False:
        profile.free_preference = _clamp((profile.free_preference or 0.0) - price_delta)

    # ── 4. Interaction counts ─────────────────────────────────────────
    if response == "yes":
        profile.total_yes = (profile.total_yes or 0) + 1
    elif response == "no":
        profile.total_no = (profile.total_no or 0) + 1
    elif response == "maybe":
        profile.total_maybe = (profile.total_maybe or 0) + 1

    profile.updated_at = datetime.now(tz=timezone.utc)
