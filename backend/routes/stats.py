from fastapi import APIRouter
from typing import Optional
import httpx

from db import (
    db, now_iso, logger,
    AGENTMAIL_API_KEY, AGENTMAIL_BASE_URL, AGENTMAIL_HEADERS,
    resolve_inbox_brand,
)
from seed import seed_database

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Mission Control API"}


@router.post("/seed")
async def seed():
    result = await seed_database()
    return result


@router.get("/inboxes")
async def get_inboxes(brand: Optional[str] = None):
    query = {}
    if brand and brand != "all":
        query["brand"] = brand
    inboxes = await db.inboxes.find(query, {"_id": 0}).to_list(100)
    return inboxes


@router.get("/stats")
async def get_stats(brand: Optional[str] = None):
    query = {}
    if brand and brand != "all":
        query["brand"] = brand

    pending_query = {**query, "status": "pending"}
    pending_approvals = await db.approvals.count_documents(pending_query)

    active_query = {**query, "status": "active"}
    active_agents = await db.agents.count_documents(active_query)
    total_agents = await db.agents.count_documents(query)

    open_query = {**query, "status": {"$in": ["open", "in_progress", "approval"]}}
    open_tasks = await db.tasks.count_documents(open_query)

    pending_emails = 0
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(f"{AGENTMAIL_BASE_URL}/inboxes", headers=AGENTMAIL_HEADERS)
            if resp.status_code == 200:
                inboxes_data = resp.json().get("inboxes", [])
                for inbox in inboxes_data:
                    inbox_brand = resolve_inbox_brand(inbox.get("email", ""))
                    if brand and brand != "all" and inbox_brand != brand:
                        continue
                    inbox_id = inbox.get("inbox_id", "")
                    msg_resp = await http.get(
                        f"{AGENTMAIL_BASE_URL}/inboxes/{inbox_id}/messages",
                        headers=AGENTMAIL_HEADERS,
                        params={"limit": 50}
                    )
                    if msg_resp.status_code == 200:
                        pending_emails += msg_resp.json().get("count", 0)
    except Exception as e:
        logger.warning(f"AgentMail stats fetch failed: {e}")
        inbox_pipeline = [{"$match": query}, {"$group": {"_id": None, "total": {"$sum": "$pending_count"}}}]
        inbox_result = await db.inboxes.aggregate(inbox_pipeline).to_list(1)
        pending_emails = inbox_result[0]["total"] if inbox_result else 0

    return {
        "pending_approvals": pending_approvals,
        "active_agents": active_agents,
        "total_agents": total_agents,
        "open_tasks": open_tasks,
        "pending_emails": pending_emails,
    }
