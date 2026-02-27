# Radar — Philadelphia Event Scout

> Stop doing the same thing every day. Radar finds what's actually worth doing.

Radar scrapes Philadelphia's best event platforms, aggregates and deduplicates them, and pushes them to your calendar. It also lets local businesses submit exclusive events that only Radar subscribers see.

---

## What Radar covers

| Source | What it scrapes |
|---|---|
| **Luma** | Tech meetups, creative gatherings, community events |
| **Philadelphia Film Festival** | Screenings, Q&As, film society programming |
| **Philadelphia Museum of Art** | Openings, lectures, member nights |
| **The Barnes Foundation** | Exhibitions, talks, tours |
| **The Franklin Institute** | Science events, IMAX, special exhibits |
| **Visit Philadelphia** | City-wide festivals, outdoor events, markets |
| **Eventbrite** | Everything else — concerts, workshops, food events |
| **Partner events** | Exclusive events from local business partners |

---

## Architecture

```
radar/
├── scrapers/
│   ├── base.py               # RawEvent dataclass + BaseScraper interface
│   ├── luma.py               # Luma public API scraper
│   ├── philly_film_festival.py
│   ├── museums.py            # PMA, Barnes, Franklin
│   ├── best_of_city.py       # VisitPhilly + Eventbrite
│   └── aggregator.py         # Runs all scrapers, deduplicates, upserts to DB
├── api/
│   ├── main.py               # FastAPI app
│   ├── schemas.py            # Pydantic models
│   └── routes/
│       ├── events.py         # GET /events, GET /events/feed.ics
│       ├── partners.py       # Partner registration + event submission
│       └── sync.py           # POST /admin/sync (manual trigger)
├── calendar_push/
│   ├── google_calendar.py    # OAuth2 push to Google Calendar
│   └── ical.py               # Standards-compliant .ics feed generator
├── scheduler/
│   └── jobs.py               # APScheduler — scrapes every N minutes
├── db/
│   └── models.py             # SQLAlchemy models (Event, Partner)
├── config.py                 # Settings from environment
├── main.py                   # Entrypoint (server + scheduler)
└── requirements.txt
```

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers (for JS-heavy sites)
playwright install chromium

# 3. Configure environment
cp .env.example .env
# edit .env with your settings

# 4. Run
python main.py
```

The API runs at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

---

## API endpoints

### Events

| Method | Path | Description |
|---|---|---|
| `GET` | `/events` | List events (filterable by category, source, date, keyword) |
| `GET` | `/events/{id}` | Single event |
| `GET` | `/events/feed.ics` | Subscribe this URL in Apple Calendar / Google Calendar / Outlook |

**Example filters:**
```
GET /events?category=film&is_free=true&start_after=2025-03-01
GET /events?search=jazz&is_exclusive=true
GET /events/feed.ics?category=arts
```

### Partner API (for local businesses)

| Method | Path | Description |
|---|---|---|
| `POST` | `/partners/register` | Register your business, receive an API key |
| `GET` | `/partners/me` | Your partner profile |
| `POST` | `/partners/events` | Submit an exclusive event |
| `GET` | `/partners/events` | Your submitted events |
| `DELETE` | `/partners/events/{id}` | Remove an event |

Use `X-Api-Key: <your_key>` header for authenticated partner routes.

### Admin

| Method | Path | Description |
|---|---|---|
| `POST` | `/admin/sync` | Trigger an immediate scrape of all sources |

---

## Calendar integration

### iCal (universal — works with Apple Calendar, Outlook, Thunderbird)

Subscribe to the feed URL in your calendar app:
```
http://localhost:8000/events/feed.ics
```

Filter to just what you care about:
```
http://localhost:8000/events/feed.ics?category=film&is_free=true
```

### Google Calendar (push)

Set up Google OAuth credentials, then run:
```python
from calendar_push.google_calendar import GoogleCalendarPusher
from db.models import SessionLocal, Event

db = SessionLocal()
events = db.query(Event).all()
pusher = GoogleCalendarPusher()
pusher.push_events(events)
```

---

## Adding a new scraper

1. Create `scrapers/your_source.py`
2. Subclass `BaseScraper`, implement `scrape() -> list[RawEvent]`
3. Add your scraper instance to `ALL_SCRAPERS` in `scrapers/aggregator.py`

```python
class MyNewScraper(BaseScraper):
    name = "my_source"

    def scrape(self) -> list[RawEvent]:
        # fetch, parse, return RawEvent objects
        ...
```

---

## Partner program

Local Philadelphia businesses can partner with Radar to reach people actively
looking for things to do. Partner events appear with an exclusive badge and are
included in subscriber feeds. Register via `POST /partners/register`.
