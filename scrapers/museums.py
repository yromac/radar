"""Museum event scrapers for Philadelphia-area institutions.

Covers:
- Philadelphia Museum of Art (philamuseum.org)
- The Barnes Foundation (barnesfoundation.org)
- Franklin Institute (fi.edu)
- Penn Museum (penn.museum)
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


class _MuseumScraper(BaseScraper):
    """Shared helpers for museum scrapers."""

    name = "museum"
    base_url: str = ""
    events_path: str = "/events/"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get(self, client: httpx.Client, url: str) -> BeautifulSoup:
        resp = client.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")

    @staticmethod
    def _text(el) -> Optional[str]:
        if el is None:
            return None
        return el.get_text(separator=" ", strip=True) or None

    @staticmethod
    def _parse_iso(raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None

    def _json_ld_events(self, soup: BeautifulSoup) -> list[dict]:
        """Extract Event objects from JSON-LD script tags."""
        import json
        results = []
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, list):
                    results.extend([d for d in data if d.get("@type") == "Event"])
                elif data.get("@type") == "Event":
                    results.append(data)
            except Exception:
                pass
        return results


class PhillyMuseumOfArtScraper(_MuseumScraper):
    """Philadelphia Museum of Art — philamuseum.org/events"""

    name = "museum_pma"
    base_url = "https://www.philamuseum.org"
    events_path = "/programs"

    def scrape(self) -> list[RawEvent]:
        events = []
        with httpx.Client(headers={"User-Agent": "RadarBot/1.0"}) as client:
            soup = self._get(client, f"{self.base_url}{self.events_path}")
            for ld in self._json_ld_events(soup):
                raw = self._from_json_ld(ld, source_id_prefix="pma")
                if raw:
                    events.append(raw)

            # Also scrape card-based listing
            for card in soup.select("article.program-card, .event-card"):
                raw = self._from_card(card, "pma")
                if raw:
                    events.append(raw)
        return events

    def _from_json_ld(self, data: dict, source_id_prefix: str) -> Optional[RawEvent]:
        try:
            start_dt = self._parse_iso(data.get("startDate"))
            if not start_dt:
                return None
            loc = data.get("location", {})
            return RawEvent(
                source="museum",
                source_id=f"{source_id_prefix}-{re.sub(r'[^a-z0-9]', '-', data.get('name','').lower())}",
                title=data.get("name", "Untitled"),
                description=data.get("description"),
                url=data.get("url", self.base_url),
                image_url=(data.get("image", [None]) or [None])[0]
                if isinstance(data.get("image"), list)
                else data.get("image"),
                start_dt=start_dt,
                end_dt=self._parse_iso(data.get("endDate")),
                venue_name=loc.get("name"),
                venue_address=loc.get("address", {}).get("streetAddress"),
                category="arts",
                tags=["museum", "arts", "philadelphia"],
            )
        except Exception as exc:
            logger.warning(f"[museum] JSON-LD parse error: {exc}")
            return None

    def _from_card(self, card, prefix: str) -> Optional[RawEvent]:
        try:
            title_el = card.select_one("h2, h3, .program-title, .event-title")
            title = self._text(title_el)
            if not title:
                return None
            link = card.select_one("a[href]")
            url = self.base_url + link["href"] if link and link["href"].startswith("/") else (
                link["href"] if link else self.base_url
            )
            date_el = card.select_one("time, .date, .event-date")
            start_dt = self._parse_iso(date_el.get("datetime")) if date_el else None
            if not start_dt:
                return None
            return RawEvent(
                source="museum",
                source_id=f"{prefix}-{re.sub(r'[^a-z0-9]', '-', title.lower()[:50])}",
                title=title,
                url=url,
                start_dt=start_dt,
                venue_name="Philadelphia Museum of Art",
                venue_address="2600 Benjamin Franklin Pkwy, Philadelphia, PA 19130",
                lat=39.9656,
                lng=-75.1810,
                category="arts",
                tags=["museum", "arts", "pma"],
            )
        except Exception:
            return None


class BarnesFoundationScraper(_MuseumScraper):
    """The Barnes Foundation — barnesfoundation.org/whats-on"""

    name = "museum_barnes"
    base_url = "https://www.barnesfoundation.org"

    def scrape(self) -> list[RawEvent]:
        events = []
        with httpx.Client(headers={"User-Agent": "RadarBot/1.0"}) as client:
            soup = self._get(client, f"{self.base_url}/whats-on")
            for ld in self._json_ld_events(soup):
                raw = self._from_json_ld(ld, "barnes")
                if raw:
                    events.append(raw)
            for card in soup.select(".event-listing, .program-item, article"):
                raw = self._from_card(card, "barnes")
                if raw:
                    events.append(raw)
        return events

    def _from_json_ld(self, data: dict, prefix: str) -> Optional[RawEvent]:
        try:
            start_dt = self._parse_iso(data.get("startDate"))
            if not start_dt:
                return None
            return RawEvent(
                source="museum",
                source_id=f"{prefix}-{re.sub(r'[^a-z0-9]', '-', data.get('name','').lower()[:50])}",
                title=data.get("name", "Untitled"),
                description=data.get("description"),
                url=data.get("url", self.base_url),
                start_dt=start_dt,
                end_dt=self._parse_iso(data.get("endDate")),
                venue_name="The Barnes Foundation",
                venue_address="2025 Benjamin Franklin Pkwy, Philadelphia, PA 19130",
                lat=39.9640,
                lng=-75.1763,
                category="arts",
                tags=["museum", "arts", "barnes", "philadelphia"],
            )
        except Exception as exc:
            logger.warning(f"[barnes] parse error: {exc}")
            return None

    def _from_card(self, card, prefix: str) -> Optional[RawEvent]:
        try:
            title = self._text(card.select_one("h2, h3, .event-title"))
            if not title:
                return None
            date_el = card.select_one("time")
            start_dt = self._parse_iso(date_el.get("datetime")) if date_el else None
            if not start_dt:
                return None
            link = card.select_one("a[href]")
            url = self.base_url + link["href"] if link and link["href"].startswith("/") else self.base_url
            return RawEvent(
                source="museum",
                source_id=f"{prefix}-{re.sub(r'[^a-z0-9]', '-', title.lower()[:50])}",
                title=title,
                url=url,
                start_dt=start_dt,
                venue_name="The Barnes Foundation",
                venue_address="2025 Benjamin Franklin Pkwy, Philadelphia, PA 19130",
                lat=39.9640,
                lng=-75.1763,
                category="arts",
                tags=["museum", "barnes", "arts"],
            )
        except Exception:
            return None


class FranklinInstituteScraper(_MuseumScraper):
    """Franklin Institute — fi.edu/events"""

    name = "museum_franklin"
    base_url = "https://www.fi.edu"

    def scrape(self) -> list[RawEvent]:
        events = []
        with httpx.Client(headers={"User-Agent": "RadarBot/1.0"}) as client:
            soup = self._get(client, f"{self.base_url}/programs-events")
            for ld in self._json_ld_events(soup):
                raw = self._from_json_ld(ld, "fi")
                if raw:
                    events.append(raw)
        return events

    def _from_json_ld(self, data: dict, prefix: str) -> Optional[RawEvent]:
        try:
            start_dt = self._parse_iso(data.get("startDate"))
            if not start_dt:
                return None
            return RawEvent(
                source="museum",
                source_id=f"{prefix}-{re.sub(r'[^a-z0-9]', '-', data.get('name','').lower()[:50])}",
                title=data.get("name", "Untitled"),
                description=data.get("description"),
                url=data.get("url", self.base_url),
                start_dt=start_dt,
                end_dt=self._parse_iso(data.get("endDate")),
                venue_name="The Franklin Institute",
                venue_address="222 N 20th St, Philadelphia, PA 19103",
                lat=39.9582,
                lng=-75.1733,
                category="arts",
                tags=["museum", "science", "franklin", "philadelphia"],
            )
        except Exception as exc:
            logger.warning(f"[franklin] parse error: {exc}")
            return None


# Registry — all museum scrapers in one list
ALL_MUSEUM_SCRAPERS: list[_MuseumScraper] = [
    PhillyMuseumOfArtScraper(),
    BarnesFoundationScraper(),
    FranklinInstituteScraper(),
]
