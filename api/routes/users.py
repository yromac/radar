"""
User management, Google Calendar OAuth, event push, and response-tracking routes.

Flow
----
1. POST /users/auth/google?email=...   → returns {auth_url, state}
2. User visits auth_url, approves, Google redirects to GET /users/auth/callback
3. Callback stores token → user is connected
4. POST /users/{user_id}/push          → pushes 2 tailored events to their calendar
5. User clicks a link inside the calendar event description (yes / maybe / no)
   GET /users/respond/{push_id}/{response} → updates their profile, returns HTML
6. GET /users/{user_id}/profile        → inspect accumulated interest weights
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from db.models import get_db, User, UserProfile, EventPush
from api.schemas import UserOut, UserProfileOut, PushResult
from recommendation.engine import pick_events_for_user
from recommendation.profile import update_profile
from calendar_push.user_pusher import UserCalendarPusher
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

# Google Calendar + basic profile info
_SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


# ─── Helpers ───────────────────────────────────────────────────────────────

def _callback_uri() -> str:
    return f"{settings.app_base_url.rstrip('/')}/users/auth/callback"


def _get_flow(redirect_uri: str):
    """Build a Google OAuth2 Flow for web-server apps."""
    from google_auth_oauthlib.flow import Flow

    creds_file = settings.google_credentials_file
    if not creds_file or not os.path.exists(creds_file):
        raise HTTPException(
            status_code=503,
            detail=(
                "Google credentials not configured. "
                "Download credentials.json from Google Cloud Console and "
                "set GOOGLE_CREDENTIALS_FILE in your .env file."
            ),
        )
    return Flow.from_client_secrets_file(creds_file, scopes=_SCOPES, redirect_uri=redirect_uri)


def _ensure_profile(db: Session, user: User) -> UserProfile:
    """Return user.profile, creating it if it doesn't exist yet."""
    if not user.profile:
        profile = UserProfile(
            user_id=user.id,
            category_weights={},
            prefers_weekends=0.0,
            prefers_evenings=0.0,
            free_preference=0.0,
            total_yes=0,
            total_no=0,
            total_maybe=0,
        )
        db.add(profile)
        db.flush()
        user.profile = profile
    return user.profile


# ─── OAuth ─────────────────────────────────────────────────────────────────

@router.get("/auth/google")
def start_google_auth(
    email: str = Query(..., description="User's email address"),
):
    """
    Start the Google Calendar OAuth flow.

    Returns an `auth_url` the user (or your frontend) should open in a browser.
    After they approve, Google redirects back to `/users/auth/callback`.
    """
    flow = _get_flow(_callback_uri())
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=email,
    )
    return {"auth_url": auth_url, "state": state}


@router.get("/auth/callback")
def google_auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Google redirects here after the user approves access.

    Exchanges the auth code for tokens, upserts the User record, and
    redirects to the frontend success page.
    """
    email: str = state  # We encoded email as the OAuth state param

    try:
        flow = _get_flow(_callback_uri())
        flow.fetch_token(code=code)
        creds = flow.credentials
    except Exception as exc:
        logger.error(f"[oauth] callback error: {exc}")
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {exc}")

    # Try to get the verified email + account ID from Google
    google_account_id: Optional[str] = None
    try:
        from googleapiclient.discovery import build as gbuild
        oauth2_svc = gbuild("oauth2", "v2", credentials=creds)
        userinfo = oauth2_svc.userinfo().get().execute()
        google_account_id = userinfo.get("id")
        if userinfo.get("email"):
            email = userinfo["email"]
    except Exception:
        pass

    # Upsert user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.flush()

    user.google_token_json = creds.to_json()
    if google_account_id:
        user.google_account_id = google_account_id

    _ensure_profile(db, user)
    db.commit()
    db.refresh(user)

    logger.info(f"[oauth] user connected: {user.email} (id={user.id})")

    # Redirect to frontend — swap port 8000 → 5173 for local dev
    frontend = settings.app_base_url.rstrip("/").replace(":8000", ":5173")
    return RedirectResponse(url=f"{frontend}/subscribe?connected=1&user_id={user.id}")


# ─── Push ──────────────────────────────────────────────────────────────────

@router.post("/{user_id}/push", response_model=PushResult)
def push_events_to_user(user_id: str, db: Session = Depends(get_db)):
    """
    Pick 2 events tailored to this user and push them to their Google Calendar.

    The events are chosen based on the user's accumulated interest profile.
    New users (no prior responses) get a random diverse selection.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.google_token_json:
        raise HTTPException(
            status_code=400,
            detail="User has not connected Google Calendar. Call GET /users/auth/google first.",
        )

    _ensure_profile(db, user)
    events = pick_events_for_user(db, user)

    if not events:
        return PushResult(pushed=0, event_ids=[], message="No new upcoming events to push")

    pusher = UserCalendarPusher(user)
    pushes = pusher.push_events(db, events)

    user.last_push_at = datetime.now(tz=timezone.utc)
    db.add(user)
    db.commit()

    return PushResult(
        pushed=len(pushes),
        event_ids=[p.event_id for p in pushes],
        message=f"Pushed {len(pushes)} event(s) to {user.email}'s calendar",
    )


# ─── Respond ───────────────────────────────────────────────────────────────

@router.get("/respond/{push_id}/{response}", response_class=HTMLResponse)
def record_response(
    push_id: str,
    response: str,
    db: Session = Depends(get_db),
):
    """
    User clicks a link embedded in their calendar event description.

    Records their yes / maybe / no, updates their interest profile, and
    returns a simple HTML thank-you page (no redirect needed).
    """
    if response not in ("yes", "no", "maybe"):
        raise HTTPException(status_code=400, detail="Response must be yes, no, or maybe")

    push = db.query(EventPush).filter(EventPush.id == push_id).first()
    if not push:
        raise HTTPException(status_code=404, detail="Push record not found")

    if push.response is not None:
        return HTMLResponse(_already_responded_html())

    push.response = response
    push.responded_at = datetime.now(tz=timezone.utc)
    db.add(push)

    user = db.query(User).filter(User.id == push.user_id).first()
    profile = _ensure_profile(db, user)
    update_profile(profile, push.event, response)
    db.add(profile)

    db.commit()

    logger.info(
        f"[respond] user={user.email} response={response} event='{push.event.title}'"
    )
    return HTMLResponse(_response_html(response, push.event.title))


# ─── Read endpoints ────────────────────────────────────────────────────────

@router.get("/{user_id}/profile", response_model=UserProfileOut)
def get_profile(user_id: str, db: Session = Depends(get_db)):
    """Return the user's accumulated interest profile."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = _ensure_profile(db, user)
    db.commit()
    return profile


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    """Return basic user info."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─── HTML helpers ──────────────────────────────────────────────────────────

_STYLE = """
  body {
    font-family: system-ui, -apple-system, sans-serif;
    background: #0a0a0a;
    color: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    margin: 0;
  }
  .card {
    text-align: center;
    max-width: 440px;
    padding: 2.5rem;
  }
  .icon { font-size: 3rem; margin-bottom: 1rem; }
  h2 { color: #00FF88; margin: 0 0 0.75rem; font-size: 1.5rem; }
  p { color: #aaa; line-height: 1.6; margin: 0.25rem 0; }
  small { color: #555; }
"""


def _response_html(response: str, event_title: str) -> str:
    icons = {"yes": "✅", "maybe": "🤔", "no": "❌"}
    messages = {
        "yes":   "Awesome — we'll find more events like this for you.",
        "maybe": "Got it — we'll fine-tune your picks.",
        "no":    "Noted — we'll steer away from these.",
    }
    return f"""<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Radar</title>
  <style>{_STYLE}</style>
</head><body>
  <div class="card">
    <div class="icon">{icons[response]}</div>
    <h2>{messages[response]}</h2>
    <p><small>"{event_title}"</small></p>
    <p style="margin-top:1.5rem; color:#555;">Radar is learning your taste. You can close this tab.</p>
  </div>
</body></html>"""


def _already_responded_html() -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Radar</title>
  <style>{_STYLE}</style>
</head><body>
  <div class="card">
    <div class="icon">📡</div>
    <h2>Already recorded</h2>
    <p>You already responded to this event. Radar is on it.</p>
  </div>
</body></html>"""
