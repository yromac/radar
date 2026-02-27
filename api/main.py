"""Radar FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.models import init_db
from api.routes import events, partners, sync, users
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB tables
    init_db()
    yield
    # Shutdown: nothing needed


app = FastAPI(
    title="Radar API",
    description=(
        "Radar aggregates the best events happening in Philadelphia — "
        "from Luma meetups to museum openings, film festivals, and exclusive "
        "partner events — and pushes them to your calendar."
    ),
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router)
app.include_router(partners.router)
app.include_router(sync.router)
app.include_router(users.router)


@app.get("/", tags=["health"])
def health():
    return {
        "service": "Radar",
        "version": settings.app_version,
        "city": settings.city,
        "status": "running",
    }
