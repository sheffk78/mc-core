"""
Morning Briefs — per-brand daily briefs written by Kit via API.
Read-only from the UI, write via API.
"""

from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone

from db import db, logger

router = APIRouter()

COLLECTION = "morning_briefs"


@router.get("/briefs/{brand}")
async def get_brief(brand: str):
    """Get the latest morning brief for a brand."""
    doc = await db[COLLECTION].find_one(
        {"brand": brand},
        {"_id": 0},
        sort=[("updated_at", -1)],
    )
    if not doc:
        return {"brand": brand, "content": "", "updated_at": None}
    return doc


@router.put("/briefs/{brand}")
async def upsert_brief(brand: str, request: Request):
    """Create or update the morning brief for a brand. Called by Kit via API."""
    body = await request.json()
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    now = datetime.now(timezone.utc).isoformat()

    result = await db[COLLECTION].update_one(
        {"brand": brand},
        {"$set": {
            "brand": brand,
            "content": content,
            "updated_at": now,
            "updated_by": body.get("updated_by", "kit"),
        }},
        upsert=True,
    )

    logger.info(f"Morning brief updated for brand={brand}")
    return {
        "brand": brand,
        "content": content,
        "updated_at": now,
        "status": "created" if result.upserted_id else "updated",
    }
