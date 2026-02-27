"""Best-things-to-do scrapers for Philadelphia.

Covers event aggregators that publish curated "what's happening" lists:
- Visit Philadelphia (visitphilly.com/things-to-do/events/)
- Eventbrite Philadelphia (public API)
- DoStuff Philly (dostuffmedia.com)
"""
import logging
import re
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseScraper, RawEvent

logger = logging.getLogger(__name__)


class VisitPhillyScraper(BaseScraper):
    """Scrapes curated event listings from visitphilly.com.

    This is the official Philadelphia tourism board — they aggregate
    festivals, markets, outdoor events, and city-wide happenings.
    """

    name = "visit_philly"
    BASE = "https://www.visitphilly.com"
    EVENTS_URL = f"{BASE}/things-to-do/events/"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get(self, client: httpx.Client, url: str) -> BeautifulSoup:
        resp = client.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")

    def scrape(self) -> list[RawEvent]:
        events = []
        with httpx.Client(headers={"User-Agent": "RadarBot/1.0"}) as client:
            soup = self._get(client, self.EVENTS_URL)
            for card in soup.select("article, .event-card, .listing-card"):
                raw = self._parse_card(card)
                if raw:
                    events.append(raw)
            # JSON-LD fallback
            events.extend(self._json_ld_events(soup))
        return events

    def _parse_card(self, card) -> Optional[RawEvent]:
        try:
            title = card.select_one("h2, h3, .card-title, .listing-title")
            if not title:
                return None
            title_text = title.get_text(strip=True)

            link = card.select_one("a[href]")
            url = self.BASE + link["href"] if link and link["href"].startswith("/") else (
                link["href"] if link else self.EVENTS_URL
            )

            date_el = card.select_one("time, .date, .event-date")
            start_dt = None
            if date_el and date_el.get("datetime"):
                try:
                    start_dt = datetime.fromisoformat(date_el["datetime"].replace("Z", "+00:00"))
                except ValueError:
                    pass

            if not start_dt:
                return None

            img = card.select_one("img[src]")
            image_url = img["src"] if img else None

            return RawEvent(
                source="best_of_city",
                source_id=f"visitphilly-{re.sub(r'[^a-z0-9]', '-', title_text.lower()[:60])}",
                title=title_text,
                url=url,
                image_url=image_url,
                start_dt=start_dt,
                category="community",
                tags=["philadelphia", "things-to-do"],
            )
        except Exception:
            return None

    def _json_ld_events(self, soup: BeautifulSoup) -> list[RawEvent]:
        import json
        results = []
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") != "Event":
                        continue
                    start_dt = self._parse_iso(item.get("startDate"))
                    if not start_dt:
                        continue
                    loc = item.get("location", {})
                    results.append(RawEvent(
                        source="best_of_city",
                        source_id=f"visitphilly-ld-{re.sub(r'[^a-z0-9]', '-', item.get('name','').lower()[:50])}",
                        title=item.get("name", "Untitled"),
                        description=item.get("description"),
                        url=item.get("url", self.EVENTS_URL),
                        start_dt=start_dt,
                        end_dt=self._parse_iso(item.get("endDate")),
                        venue_name=loc.get("name"),
                        venue_address=loc.get("address", {}).get("streetAddress"),
                        category="community",
                        tags=["philadelphia", "visit-philly"],
                    ))
            except Exception:
                pass
        return results

    @staticmethod
    def _parse_iso(raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None


class EventbriteScraper(BaseScraper):
    """Scrapes Eventbrite public listings for Philadelphia via their search API.

    Uses the public search endpoint — no API key required for browsing.
    """

    name = "eventbrite"
    SEARCH_URL = "https://www.eventbrite.com/api/v3/destination/search/"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _search(self, client: httpx.Client, page: int = 1) -> dict:
        params = {
            "destination": "philadelphia--pa",
            "page": page,
            "page_size": 50,
            "include_adult_events": False,
        }
        resp = client.get(self.SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def scrape(self) -> list[RawEvent]:
        events = []
        with httpx.Client(headers={"User-Agent": "RadarBot/1.0"}) as client:
            for page in range(1, 4):  # first 3 pages = ~150 events
                try:
                    data = self._search(client, page)
                    for event_data in data.get("events", {}).get("results", []):
                        raw = self._parse(event_data)
                        if raw:
                            events.append(raw)
                    if not data.get("pagination", {}).get("has_next_page"):
                        break
                except Exception as exc:
                    logger.warning(f"[eventbrite] page {page} failed: {exc}")
                    break
        return events

    def _parse(self, e: dict) -> Optional[RawEvent]:
        try:
            start_raw = e.get("start_date") or e.get("start", {}).get("utc")
            if not start_raw:
                return None
            start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
            end_raw = e.get("end_date") or e.get("end", {}).get("utc")
            end_dt = datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else None

            is_free = e.get("is_free", False)

            return RawEvent(
                source="best_of_city",
                source_id=f"eventbrite-{e.get('id', '')}",
                title=e.get("name", {}).get("text") or e.get("name", "Untitled"),
                description=(e.get("summary") or e.get("description", {}).get("text")),
                url=e.get("url", ""),
                image_url=(e.get("logo") or {}).get("url"),
                start_dt=start_dt,
                end_dt=end_dt,
                venue_name=(e.get("venue") or {}).get("name"),
                venue_address=(e.get("venue") or {}).get("address", {}).get("localized_address_display"),
                lat=float((e.get("venue") or {}).get("latitude", 0) or 0) or None,
                lng=float((e.get("venue") or {}).get("longitude", 0) or 0) or None,
                category="community",
                tags=["eventbrite", "philadelphia"],
                is_free=is_free,
            )
        except Exception as exc:
            logger.warning(f"[eventbrite] parse error: {exc}")
            return None
