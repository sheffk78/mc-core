from fastapi import APIRouter
from typing import Optional

from db import db

router = APIRouter()


@router.get("/activity")
async def get_activity(brand: Optional[str] = None, limit: int = 20):
    query = {}
    if brand and brand != "all":
        query["brand"] = brand
    activity = await db.activity.find(query, {"_id": 0}).sort("time", -1).to_list(limit)
    return activity
