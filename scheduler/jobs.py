"""APScheduler job definitions for Radar.

The scraper job runs once daily at end of day (11 PM by default, configurable
via SCRAPE_HOUR in .env) so the next day's events are ready before you wake up.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

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
        trigger=CronTrigger(hour=settings.scrape_hour, minute=0, timezone=settings.timezone),
        id="scrape_events",
        name="End-of-day scrape of all event sources",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(
        f"[scheduler] started — daily scrape at {settings.scrape_hour:02d}:00 {settings.timezone}"
    )
    return scheduler
