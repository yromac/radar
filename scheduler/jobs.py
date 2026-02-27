"""APScheduler job definitions for Radar.

The scraper job runs on a configurable interval (default: every 60 minutes)
to keep the event database fresh without hammering source sites.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from db.models import SessionLocal
from scrapers.aggregator import sync
from config import settings

logger = logging.getLogger(__name__)


def _scrape_job():
    """Run a full scrape cycle and log the result."""
    db = SessionLocal()
    try:
        result = sync(db)
        logger.info(
            f"[scheduler] sync complete — "
            f"scraped={result['scraped']}, "
            f"created={result['created']}, "
            f"updated={result['updated']}"
        )
    except Exception as exc:
        logger.error(f"[scheduler] sync failed: {exc}", exc_info=True)
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    """Start the background scheduler and return it."""
    scheduler = BackgroundScheduler(timezone=settings.timezone)
    scheduler.add_job(
        _scrape_job,
        trigger=IntervalTrigger(minutes=settings.scrape_interval_minutes),
        id="scrape_events",
        name="Scrape all event sources",
        replace_existing=True,
        max_instances=1,  # prevent overlap if a scrape takes longer than interval
    )
    scheduler.start()
    logger.info(
        f"[scheduler] started — scraping every {settings.scrape_interval_minutes} minutes"
    )
    return scheduler
