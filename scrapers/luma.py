"""Luma (lu.ma) scraper — uses the public Luma API and HTML fallback."""
import logging
from datetime import datetime
from typing import Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseScraper, RawEvent

logger = logging.getLogger(__name__)

LUMA_API_BASE = "https://api.lu.ma/public/v1"
LUMA_CITY_SEARCH = f"{LUMA_API_BASE}/event/get-discover-events"


class LumaScraper(BaseScraper):
    """Scrapes public events in Philadelphia from Luma.

    Luma exposes a public discover endpoint that supports city-based filtering.
    No auth is required for public events.
    """

    name = "luma"

    def __init__(self, city: str = "Philadelphia", max_pages: int = 5):
        self.city = city
        self.max_pages = max_pages

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_page(self, client: httpx.Client, after: Optional[str] = None) -> dict:
        params = {
            "pagination_limit": 50,
            "geo_latitude": 39.9526,   # Philadelphia
            "geo_longitude": -75.1652,
            "geo_radius_km": 30,
            "series_mode": "next_event",
        }
        if after:
            params["pagination_cursor"] = after

        resp = client.get(LUMA_CITY_SEARCH, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def scrape(self) -> list[RawEvent]:
        events: list[RawEvent] = []
        cursor = None

        with httpx.Client(headers={"User-Agent": "RadarBot/1.0"}) as client:
            for _ in range(self.max_pages):
                data = self._fetch_page(client, after=cursor)
                entries = data.get("entries", [])

                for entry in entries:
                    event = entry.get("event", {})
                    raw = self._parse_event(event)
                    if raw:
                        events.append(raw)

                pagination = data.get("pagination_cursor")
                if not pagination or not entries:
                    break
                cursor = pagination

        return events

    def _parse_event(self, event: dict) -> Optional[RawEvent]:
        try:
            start_str = event.get("start_at") or event.get("start_time")
            if not start_str:
                return None

            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = None
            if end_str := event.get("end_at") or event.get("end_time"):
                end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

            geo = event.get("geo_address_json") or {}
            tickets = event.get("ticket_info") or {}

            is_free = tickets.get("is_free", True)
            price_min = None
            price_max = None
            if not is_free:
                price_min = tickets.get("min_ticket_price")
                price_max = tickets.get("max_ticket_price")

            return RawEvent(
                source="luma",
                source_id=event.get("api_id", event.get("id", "")),
                title=event.get("name", "Untitled"),
                description=event.get("description"),
                url=f"https://lu.ma/{event.get('url', '')}",
                image_url=event.get("cover_url"),
                start_dt=start_dt,
                end_dt=end_dt,
                venue_name=geo.get("full_address"),
                venue_address=geo.get("full_address"),
                lat=geo.get("latitude"),
                lng=geo.get("longitude"),
                category=self._map_category(event.get("tags", [])),
                tags=event.get("tags", []),
                is_free=is_free,
                price_min=price_min,
                price_max=price_max,
            )
        except Exception as exc:
            logger.warning(f"[luma] failed to parse event: {exc}")
            return None

    @staticmethod
    def _map_category(tags: list[str]) -> str:
        tag_set = {t.lower() for t in tags}
        if tag_set & {"tech", "startup", "ai", "web3", "developer"}:
            return "tech"
        if tag_set & {"music", "concert", "dj", "live"}:
            return "music"
        if tag_set & {"art", "gallery", "exhibition"}:
            return "arts"
        if tag_set & {"food", "dinner", "tasting", "restaurant"}:
            return "food"
        if tag_set & {"film", "movie", "cinema", "screening"}:
            return "film"
        if tag_set & {"fitness", "yoga", "wellness", "meditation"}:
            return "wellness"
        if tag_set & {"outdoor", "hike", "nature"}:
            return "outdoor"
        return "community"
