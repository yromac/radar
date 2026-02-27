"""Admin sync route — triggers a manual scrape cycle."""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from db.models import get_db
from api.schemas import SyncResult
from scrapers.aggregator import sync
from config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_key: Optional[str] = Header(None)):
    if not settings.partner_api_key:
        return  # admin key not configured — open in dev mode
    if x_admin_key != settings.partner_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/sync", response_model=SyncResult)
def trigger_sync(
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    """Manually trigger a full scrape and DB sync.

    In production this runs automatically on a schedule, but you can
    call this endpoint to force an immediate refresh.
    """
    result = sync(db)
    return result
