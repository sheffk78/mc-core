"""
Google Calendar integration via Service Account.
No OAuth redirect flow — authenticates server-side with a JSON key.
The calendar must be shared with the service account email.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from datetime import datetime, timezone, timedelta
import os
import uuid

from google.oauth2 import service_account
from googleapiclient.discovery import build

from db import logger

# ── Config from env ──

GOOGLE_CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "")
SA_CLIENT_EMAIL = os.environ.get("GOOGLE_SA_CLIENT_EMAIL", "")
SA_PRIVATE_KEY = os.environ.get("GOOGLE_SA_PRIVATE_KEY", "").replace("\\n", "\n")
SA_PROJECT_ID = os.environ.get("GOOGLE_SA_PROJECT_ID", "")
SA_TOKEN_URI = os.environ.get("GOOGLE_SA_TOKEN_URI", "https://oauth2.googleapis.com/token")

SCOPES = ["https://www.googleapis.com/auth/calendar"]

router = APIRouter()

# ── Service Account credentials ──

def _get_credentials():
    """Build service account credentials from env vars."""
    if not SA_CLIENT_EMAIL or not SA_PRIVATE_KEY:
        return None

    info = {
        "type": "service_account",
        "project_id": SA_PROJECT_ID,
        "private_key_id": os.environ.get("GOOGLE_SA_PRIVATE_KEY_ID", ""),
        "private_key": SA_PRIVATE_KEY,
        "client_email": SA_CLIENT_EMAIL,
        "client_id": os.environ.get("GOOGLE_SA_CLIENT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": SA_TOKEN_URI,
    }
    try:
        creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        return creds
    except Exception as e:
        logger.error(f"Failed to build service account credentials: {e}")
        return None


def _get_service():
    """Build a Google Calendar API service object."""
    creds = _get_credentials()
    if not creds:
        return None
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


# ── Status (replaces OAuth status check) ──

@router.get("/oauth/calendar/status")
async def calendar_status():
    """Check if calendar is configured via service account."""
    if not SA_CLIENT_EMAIL or not SA_PRIVATE_KEY or not GOOGLE_CALENDAR_ID:
        return {"connected": False, "accounts": []}

    return {
        "connected": True,
        "accounts": [{
            "id": "service-account",
            "email": GOOGLE_CALENDAR_ID,
            "name": GOOGLE_CALENDAR_ID,
            "picture": "",
            "connected_at": "",
            "color": "#c85a2a",
            "auth_type": "service_account",
            "service_account_email": SA_CLIENT_EMAIL,
        }],
    }


# ── OAuth stubs (no-ops, frontend may still call these) ──

@router.get("/oauth/calendar/login")
async def calendar_login_stub():
    """Service account doesn't need OAuth login."""
    return {"message": "Calendar uses service account authentication. No login needed.", "connected": True}


@router.delete("/oauth/calendar/disconnect/{account_id}")
async def calendar_disconnect_stub(account_id: str):
    """Service account can't be disconnected from UI."""
    return {"message": "Service account calendar cannot be disconnected from UI. Remove env vars to disconnect.", "status": "no_op"}


# ── Calendar Events ──

@router.get("/calendar/events")
async def get_calendar_events(days_ahead: int = 14, days_behind: int = 7):
    """Fetch events from the configured Google Calendar."""
    service = _get_service()
    if not service:
        return {"events": [], "accounts": 0, "error": "Calendar not configured. Check service account env vars."}

    cal_id = GOOGLE_CALENDAR_ID

    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=days_behind)).isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    all_events = []

    try:
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=200,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        for ev in events_result.get("items", []):
            if ev.get("status") == "cancelled":
                continue

            start = ev.get("start", {})
            end = ev.get("end", {})
            is_all_day = "date" in start and "dateTime" not in start

            all_events.append({
                "id": ev.get("id", str(uuid.uuid4())),
                "google_event_id": ev.get("id", ""),
                "calendar_id": cal_id,
                "title": ev.get("summary", "(No title)"),
                "description": ev.get("description", ""),
                "location": ev.get("location", ""),
                "start": start.get("dateTime", start.get("date", "")),
                "end": end.get("dateTime", end.get("date", "")),
                "all_day": is_all_day,
                "color": ev.get("colorId", "#c85a2a"),
                "calendar_name": "Calendar",
                "account_email": GOOGLE_CALENDAR_ID,
                "account_name": GOOGLE_CALENDAR_ID,
                "attendees": [a.get("email", "") for a in ev.get("attendees", [])],
                "html_link": ev.get("htmlLink", ""),
                "hangout_link": ev.get("hangoutLink", ""),
                "conference_data": _extract_conference(ev.get("conferenceData")),
                "creator": ev.get("creator", {}).get("email", ""),
                "organizer": ev.get("organizer", {}).get("displayName", ev.get("organizer", {}).get("email", "")),
                "status": ev.get("status", "confirmed"),
            })

    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return {"events": [], "accounts": 1, "error": str(e)}

    all_events.sort(key=lambda x: x.get("start", ""))
    return {"events": all_events, "accounts": 1}


def _extract_conference(conf_data):
    if not conf_data:
        return None
    entry_points = conf_data.get("entryPoints", [])
    for ep in entry_points:
        if ep.get("entryPointType") == "video":
            return {"type": "video", "uri": ep.get("uri", ""), "label": ep.get("label", "Join")}
    return None


@router.post("/calendar/events")
async def create_calendar_event(request: Request):
    """Create a new event on Google Calendar."""
    service = _get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Calendar not configured")

    body = await request.json()
    cal_id = body.get("calendar_id", GOOGLE_CALENDAR_ID)
    is_all_day = body.get("all_day", False)

    event_body = {
        "summary": body.get("title", ""),
        "description": body.get("description", ""),
        "location": body.get("location", ""),
    }

    if is_all_day:
        event_body["start"] = {"date": body["start"][:10]}
        event_body["end"] = {"date": body.get("end", body["start"])[:10]}
    else:
        event_body["start"] = {"dateTime": body["start"], "timeZone": body.get("timezone", "America/Denver")}
        event_body["end"] = {"dateTime": body["end"], "timeZone": body.get("timezone", "America/Denver")}

    if body.get("attendees"):
        event_body["attendees"] = [{"email": e} for e in body["attendees"]]

    try:
        created = service.events().insert(calendarId=cal_id, body=event_body).execute()
        return {
            "id": created.get("id"),
            "status": "created",
            "html_link": created.get("htmlLink", ""),
        }
    except Exception as e:
        logger.error(f"Create event error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.put("/calendar/events/{event_id}")
async def update_calendar_event(event_id: str, request: Request):
    """Update an existing Google Calendar event."""
    service = _get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Calendar not configured")

    body = await request.json()
    cal_id = body.get("calendar_id", GOOGLE_CALENDAR_ID)
    is_all_day = body.get("all_day", False)

    event_body = {}
    if "title" in body:
        event_body["summary"] = body["title"]
    if "description" in body:
        event_body["description"] = body["description"]
    if "location" in body:
        event_body["location"] = body["location"]
    if "start" in body:
        if is_all_day:
            event_body["start"] = {"date": body["start"][:10]}
        else:
            event_body["start"] = {"dateTime": body["start"], "timeZone": body.get("timezone", "America/Denver")}
    if "end" in body:
        if is_all_day:
            event_body["end"] = {"date": body["end"][:10]}
        else:
            event_body["end"] = {"dateTime": body["end"], "timeZone": body.get("timezone", "America/Denver")}

    try:
        updated = service.events().patch(calendarId=cal_id, eventId=event_id, body=event_body).execute()
        return {
            "id": updated.get("id"),
            "status": "updated",
            "html_link": updated.get("htmlLink", ""),
        }
    except Exception as e:
        logger.error(f"Update event error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str, calendar_id: str = ""):
    """Delete a Google Calendar event."""
    service = _get_service()
    if not service:
        raise HTTPException(status_code=500, detail="Calendar not configured")

    cal_id = calendar_id or GOOGLE_CALENDAR_ID

    try:
        service.events().delete(calendarId=cal_id, eventId=event_id).execute()
        return {"status": "deleted", "event_id": event_id}
    except Exception as e:
        logger.error(f"Delete event error: {e}")
        raise HTTPException(status_code=502, detail=str(e))


# Legacy feed endpoints
@router.get("/calendar/feeds")
async def list_calendar_feeds():
    return []


@router.post("/calendar/feeds")
async def add_calendar_feed_legacy():
    return {"message": "Calendar uses service account. No feeds needed."}


@router.delete("/calendar/feeds/{feed_id}")
async def delete_calendar_feed(feed_id: str):
    return {"status": "no_op"}
