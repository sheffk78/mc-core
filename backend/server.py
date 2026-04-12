from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
import os
import json
import asyncio
import httpx
from datetime import datetime, timezone, timedelta

from db import (
    db, client, ws_manager, logger, now_iso,
    AGENTMAIL_API_KEY, AGENTMAIL_BASE_URL, AGENTMAIL_HEADERS,
    SYNC_INTERVAL_SECONDS, resolve_inbox_brand,
)
from models import ApprovalItem, ActivityEntry
from seed import seed_database

from routes.tasks import router as tasks_router
from routes.approvals import router as approvals_router
from routes.schedule import router as schedule_router
from routes.agentmail import router as agentmail_router
from routes.users import router as users_router
from routes.brands import router as brands_router
from routes.calendar import router as calendar_router
from routes.activity import router as activity_router
from routes.templates import router as templates_router
from routes.stats import router as stats_router
from routes.briefs import router as briefs_router

app = FastAPI()

# Mount all route modules under /api/v1
api_router = APIRouter(prefix="/api/v1")
api_router.include_router(stats_router)
api_router.include_router(tasks_router)
api_router.include_router(approvals_router)
api_router.include_router(schedule_router)
api_router.include_router(agentmail_router)
api_router.include_router(users_router)
api_router.include_router(brands_router)
api_router.include_router(calendar_router)
api_router.include_router(activity_router)
api_router.include_router(briefs_router)
api_router.include_router(templates_router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Background Tasks ===

_sync_task = None

async def _do_incremental_sync():
    if not AGENTMAIL_API_KEY:
        return 0
    new_count = 0
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.get(f"{AGENTMAIL_BASE_URL}/inboxes", headers=AGENTMAIL_HEADERS)
            if resp.status_code != 200:
                return 0
            inbox_list = resp.json().get("inboxes", [])

            for inbox in inbox_list:
                inbox_id = inbox.get("inbox_id", "")
                inbox_email = inbox.get("email", "")
                display_name = inbox.get("display_name", "")
                brand = resolve_inbox_brand(inbox_email)

                msg_resp = await http.get(
                    f"{AGENTMAIL_BASE_URL}/inboxes/{inbox_id}/messages",
                    headers=AGENTMAIL_HEADERS, params={"limit": 20}
                )
                if msg_resp.status_code != 200:
                    continue

                messages = msg_resp.json().get("messages", [])
                for msg in messages:
                    msg_id = msg.get("message_id", "")
                    exists = await db.approvals.find_one({"agentmail_message_id": msg_id})
                    act_exists = await db.activity.find_one({"agentmail_message_id": msg_id})
                    if exists and act_exists:
                        continue

                    labels = msg.get("labels", [])
                    is_received = "received" in labels
                    is_sent = "sent" in labels
                    is_unread = "unread" in labels
                    subject = msg.get("subject", "(no subject)")
                    from_addr = msg.get("from_", msg.get("from", ""))
                    to_list = msg.get("to", [])
                    to_str = ", ".join(to_list) if isinstance(to_list, list) else str(to_list)
                    text = msg.get("extracted_text") or msg.get("text") or ""
                    created_at = msg.get("created_at", now_iso())

                    if is_received and not is_sent and not exists:
                        approval = ApprovalItem(
                            brand=brand, type="email", agent_name=display_name,
                            from_address=inbox_email, to_address=str(from_addr),
                            inbox=inbox_id, subject=subject,
                            preview=text[:500] if text else f"From: {from_addr}",
                            created_at=str(created_at),
                            status="pending" if is_unread else "reviewed",
                        )
                        doc = approval.model_dump()
                        doc["agentmail_message_id"] = msg_id
                        doc["agentmail_thread_id"] = msg.get("thread_id", "")
                        await db.approvals.insert_one(doc)
                        new_count += 1

                    if not act_exists:
                        act_type = "email_in" if is_received else "email_out" if is_sent else "system"
                        act_text = f"{'Received' if is_received else 'Sent'}: {subject}"
                        entry = ActivityEntry(
                            brand=brand, type=act_type, text=act_text,
                            detail=f"{'From' if is_received else 'To'}: {from_addr if is_received else to_str}",
                            time=str(created_at),
                        )
                        doc = entry.model_dump()
                        doc["agentmail_message_id"] = msg_id
                        await db.activity.insert_one(doc)
    except Exception as e:
        logger.warning(f"Incremental sync error: {e}")
    return new_count


async def _auto_sync_loop():
    await asyncio.sleep(5)
    while True:
        try:
            new = await _do_incremental_sync()
            if new > 0:
                logger.info(f"Auto-sync: {new} new messages imported")
        except Exception as e:
            logger.warning(f"Auto-sync loop error: {e}")
        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


# === Lifecycle Events ===

@app.on_event("startup")
async def startup():
    global _sync_task
    count = await db.brands.count_documents({})
    if count == 0:
        await seed_database()
        logger.info("Database seeded on startup")

    if AGENTMAIL_API_KEY:
        try:
            approval_count = await db.approvals.count_documents({"agentmail_message_id": {"$exists": True}})
            if approval_count == 0:
                async with httpx.AsyncClient(timeout=15) as http:
                    resp = await http.get(f"{AGENTMAIL_BASE_URL}/inboxes", headers=AGENTMAIL_HEADERS)
                    if resp.status_code == 200:
                        inbox_list = resp.json().get("inboxes", [])
                        await db.approvals.delete_many({})
                        await db.activity.delete_many({})
                        for inbox in inbox_list:
                            inbox_id = inbox.get("inbox_id", "")
                            inbox_email = inbox.get("email", "")
                            display_name = inbox.get("display_name", "")
                            brand = resolve_inbox_brand(inbox_email)
                            msg_resp = await http.get(
                                f"{AGENTMAIL_BASE_URL}/inboxes/{inbox_id}/messages",
                                headers=AGENTMAIL_HEADERS, params={"limit": 20}
                            )
                            if msg_resp.status_code != 200:
                                continue
                            messages = msg_resp.json().get("messages", [])
                            for msg in messages:
                                labels = msg.get("labels", [])
                                is_received = "received" in labels
                                is_sent = "sent" in labels
                                is_unread = "unread" in labels
                                subject = msg.get("subject", "(no subject)")
                                from_addr = msg.get("from_", msg.get("from", ""))
                                to_list = msg.get("to", [])
                                to_str = ", ".join(to_list) if isinstance(to_list, list) else str(to_list)
                                text = msg.get("extracted_text") or msg.get("text") or ""
                                created_at = msg.get("created_at", now_iso())
                                if is_received and not is_sent:
                                    approval = ApprovalItem(
                                        brand=brand, type="email", agent_name=display_name,
                                        from_address=inbox_email, to_address=str(from_addr),
                                        inbox=inbox_id, subject=subject,
                                        preview=text[:500] if text else f"From: {from_addr}",
                                        created_at=str(created_at),
                                        status="pending" if is_unread else "reviewed",
                                    )
                                    doc = approval.model_dump()
                                    doc["agentmail_message_id"] = msg.get("message_id", "")
                                    doc["agentmail_thread_id"] = msg.get("thread_id", "")
                                    await db.approvals.insert_one(doc)
                                act_type = "email_in" if is_received else "email_out" if is_sent else "system"
                                act_text = f"{'Received' if is_received else 'Sent'}: {subject}"
                                entry = ActivityEntry(
                                    brand=brand, type=act_type, text=act_text,
                                    detail=f"{'From' if is_received else 'To'}: {from_addr if is_received else to_str}",
                                    time=str(created_at),
                                )
                                doc = entry.model_dump()
                                doc["agentmail_message_id"] = msg.get("message_id", "")
                                await db.activity.insert_one(doc)
                        logger.info("AgentMail data synced on startup")
        except Exception as e:
            logger.warning(f"AgentMail startup sync failed: {e}")

    if AGENTMAIL_API_KEY:
        _sync_task = asyncio.create_task(_auto_sync_loop())
        logger.info(f"Auto-sync started (every {SYNC_INTERVAL_SECONDS}s)")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# === WebSocket Endpoint ===

@app.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                msg_type = msg.get("type", "")
                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif msg_type == "sync_state":
                    approvals = await db.approvals.find({"status": "pending"}, {"_id": 0}).sort("created_at", -1).to_list(50)
                    tasks = await db.tasks.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
                    activity = await db.activity.find({}, {"_id": 0}).sort("time", -1).to_list(50)
                    await websocket.send_text(json.dumps({
                        "type": "sync_state",
                        "data": {
                            "approvalQueue": approvals,
                            "actionItems": tasks,
                            "activity": activity,
                        }
                    }))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


# Backward-compatible root health endpoint
@app.get("/api")
@app.get("/api/")
async def api_root_redirect():
    return {"message": "Mission Control API", "version": "v1", "base": "/api/v1"}
