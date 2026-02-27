"""Radar — main entrypoint.

Starts the FastAPI server with the background scrape scheduler running
alongside it.

Usage:
    python main.py

Or with uvicorn directly (scheduler won't auto-start in that case,
use the /admin/sync endpoint or run the scheduler separately):
    uvicorn api.main:app --reload
"""
import logging
import uvicorn
from api.main import app
from scheduler.jobs import start_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    scheduler = start_scheduler()
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    finally:
        scheduler.shutdown()
