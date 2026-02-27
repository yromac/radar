"""Philadelphia Film Festival / Philadelphia Film Society scraper.

Scrapes the public event listings from https://filmadelphia.org/events/
using HTML parsing. The site renders server-side HTML, so no JS engine needed.
"""
import logging
import re
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import BaseScraper, RawEvent

logger = logging.getLogger(__name__)

PHILLY_FILM_BASE = "https://filmadelphia.org"
EVENTS_URL = f"{PHILLY_FILM_BASE}/events/"
TZ = ZoneInfo("America/New_York")


class PhillyFilmFestivalScraper(BaseScraper):
    """Scrapes film screenings and events from filmadelphia.org (Philadelphia
    Film Society). Covers the Philadelphia Film Festival and year-round
    programming at their theaters."""

    name = "philly_film_festival"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get_page(self, client: httpx.Client, url: str) -> BeautifulSoup:
        resp = client.get(url, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")

    def scrape(self) -> list[RawEvent]:
        events: list[RawEvent] = []

        with httpx.Client(headers={"User-Agent": "RadarBot/1.0"}) as client:
            soup = self._get_page(client, EVENTS_URL)
            event_links = self._collect_event_links(soup)
            logger.info(f"[philly_film_festival] found {len(event_links)} event pages")

            for url in event_links:
                raw = self._scrape_event_page(client, url)
                if raw:
                    events.append(raw)

        return events

    def _collect_event_links(self, soup: BeautifulSoup) -> list[str]:
        """Find all individual event page URLs from the listings page."""
        links = []
        for a in soup.select("a[href]"):
            href = a["href"]
            # filmadelphia event pages follow /events/<slug>/ pattern
            if re.match(r"^/events/[^/]+/$", href) or re.match(
                r"^https://filmadelphia\.org/events/[^/]+/$", href
            ):
                full = href if href.startswith("http") else f"{PHILLY_FILM_BASE}{href}"
                if full not in links:
                    links.append(full)
        return links

    def _scrape_event_page(self, client: httpx.Client, url: str) -> Optional[RawEvent]:
        try:
            soup = self._get_page(client, url)

            title = self._text(soup.select_one("h1.entry-title, h1.event-title, h1"))
            if not title:
                return None

            description = self._text(
                soup.select_one(".entry-content, .event-description, .tribe-events-content")
            )

            # Try structured date/time fields first (Tribe Events plugin)
            start_dt = self._parse_tribe_dt(soup, "start") or self._parse_meta_dt(
                soup, "startDate"
            )
            end_dt = self._parse_tribe_dt(soup, "end") or self._parse_meta_dt(soup, "endDate")

            if not start_dt:
                return None

            venue = soup.select_one(".tribe-venue, .event-venue")
            venue_name = self._text(venue.select_one(".tribe-venue-location, .venue-name") if venue else None)
            venue_address = self._text(
                venue.select_one(".tribe-venue-address, address") if venue else None
            )

            image_url = None
            if og_img := soup.select_one('meta[property="og:image"]'):
                image_url = og_img.get("content")

            slug = url.rstrip("/").split("/")[-1]

            return RawEvent(
                source="philly_film_festival",
                source_id=slug,
                title=title,
                description=description,
                url=url,
                image_url=image_url,
                start_dt=start_dt,
                end_dt=end_dt,
                venue_name=venue_name or "Philadelphia Film Society",
                venue_address=venue_address,
                category="film",
                tags=["film", "philadelphia", "cinema"],
            )
        except Exception as exc:
            logger.warning(f"[philly_film_festival] error scraping {url}: {exc}")
            return None

    def _parse_tribe_dt(self, soup: BeautifulSoup, which: str) -> Optional[datetime]:
        """Parse The Events Calendar (Tribe) plugin datetime attributes."""
        sel = f"abbr.tribe-events-abbr.tribe-events-{which}, time.tribe-events-{which}"
        el = soup.select_one(sel)
        if el and el.get("title"):
            try:
                return datetime.fromisoformat(el["title"])
            except ValueError:
                pass
        return None

    def _parse_meta_dt(self, soup: BeautifulSoup, prop: str) -> Optional[datetime]:
        el = soup.select_one(f'meta[itemprop="{prop}"]')
        if el and el.get("content"):
            try:
                raw = el["content"].replace("Z", "+00:00")
                return datetime.fromisoformat(raw)
            except ValueError:
                pass
        return None

    @staticmethod
    def _text(el) -> Optional[str]:
        if el is None:
            return None
        return el.get_text(separator=" ", strip=True) or None
