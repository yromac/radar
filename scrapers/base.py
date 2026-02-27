"""Base scraper interface that all platform scrapers implement."""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RawEvent:
    """Platform-agnostic event returned by every scraper."""
    source: str
    source_id: str
    title: str
    start_dt: datetime
    url: str

    description: Optional[str] = None
    image_url: Optional[str] = None
    end_dt: Optional[datetime] = None
    all_day: bool = False

    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    category: str = "other"
    tags: list[str] = field(default_factory=list)

    is_free: Optional[bool] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None


class BaseScraper(ABC):
    """All scrapers inherit from this. Each implements `scrape()` and returns
    a list of RawEvent objects."""

    name: str = "base"

    def run(self) -> list[RawEvent]:
        try:
            logger.info(f"[{self.name}] starting scrape")
            events = self.scrape()
            logger.info(f"[{self.name}] found {len(events)} events")
            return events
        except Exception as exc:
            logger.error(f"[{self.name}] scrape failed: {exc}", exc_info=True)
            return []

    @abstractmethod
    def scrape(self) -> list[RawEvent]:
        """Fetch and return raw events from the platform."""
        ...
