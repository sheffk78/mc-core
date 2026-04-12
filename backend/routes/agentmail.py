from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import os
import httpx

from db import (
    db, ws_manager, now_iso, logger,
    AGENTMAIL_API_KEY, AGENTMAIL_BASE_URL, AGENTMAIL_HEADERS,
    INBOX_BRAND_MAP, resolve_inbox_brand,
)
from models import (
    LabelUpdate, ComposeEmail, ReplyEmail, ActivityEntry,
)

router = APIRouter()


@router.post("/agentmail/sync")
async def sync_agentmail():
    synced_activity = 0

    try:
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.get(f"{AGENTMAIL_BASE_URL}/inboxes", headers=AGENTMAIL_HEADERS)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to fetch inboxes")
            inbox_list = resp.json().get("inboxes", [])

            await db.activity.delete_many({})

            for inbox in inbox_list:
                inbox_id = inbox.get("inbox_id", "")
                inbox_email = inbox.get("email", "")
                brand = resolve_inbox_brand(inbox_email)

                msg_resp = await http.get(
                    f"{AGENTMAIL_BASE_URL}/inboxes/{inbox_id}/messages",
                    headers=AGENTMAIL_HEADERS,
                    params={"limit": 20}
                )
                if msg_resp.status_code != 200:
                    continue

                messages = msg_resp.json().get("messages", [])
                for msg in messages:
                    labels = msg.get("labels", [])
                    subject = msg.get("subject", "(no subject)")
                    from_addr = msg.get("from_", msg.get("from", ""))
                    to_list = msg.get("to", [])
                    to_str = ", ".join(to_list) if isinstance(to_list, list) else str(to_list)
                    created_at = msg.get("created_at", now_iso())
                    is_received = "received" in labels
                    is_sent = "sent" in labels

                    act_type = "email_in" if is_received else "email_out" if is_sent else "system"
                    act_text = f"{'Received' if is_received else 'Sent'}: {subject}" if is_received or is_sent else subject
                    entry = ActivityEntry(
                        brand=brand, type=act_type, text=act_text,
                        detail=f"{'From' if is_received else 'To'}: {from_addr if is_received else to_str}",
                        time=str(created_at),
                    )
                    await db.activity.insert_one(entry.model_dump())
                    synced_activity += 1

        return {
            "status": "synced",
            "activity_entries": synced_activity,
            "inboxes_scanned": len(inbox_list),
        }
    except httpx.HTTPError as e:
        logger.error(f"AgentMail sync error: {e}")
        raise HTTPException(status_code=502, detail=f"Sync failed: {e}")


@router.get("/agentmail/inboxes")
async def get_agentmail_inboxes(brand: Optional[str] = None):
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(f"{AGENTMAIL_BASE_URL}/inboxes", headers=AGENTMAIL_HEADERS)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="AgentMail API error")
            data = resp.json()
            inboxes = []
            for inbox in data.get("inboxes", []):
                inbox_brand = resolve_inbox_brand(inbox.get("email", ""))
                if brand and brand != "all" and inbox_brand != brand:
                    continue
                msg_resp = await http.get(
                    f"{AGENTMAIL_BASE_URL}/inboxes/{inbox['inbox_id']}/messages",
                    headers=AGENTMAIL_HEADERS,
                    params={"limit": 50}
                )
                msg_count = 0
                last_message_time = None
                if msg_resp.status_code == 200:
                    msg_data = msg_resp.json()
                    msg_count = msg_data.get("count", 0)
                    messages = msg_data.get("messages", [])
                    if messages:
                        last_message_time = messages[0].get("created_at", "")
                inboxes.append({
                    "inbox_id": inbox.get("inbox_id", ""),
                    "email": inbox.get("email", ""),
                    "display_name": inbox.get("display_name", ""),
                    "brand": inbox_brand,
                    "message_count": msg_count,
                    "last_activity": last_message_time or inbox.get("created_at", ""),
                    "created_at": inbox.get("created_at", ""),
                })
            return inboxes
    except httpx.HTTPError as e:
        logger.error(f"AgentMail API error: {e}")
        raise HTTPException(status_code=502, detail="Failed to connect to AgentMail")


@router.get("/agentmail/inboxes/{inbox_id}/messages")
async def get_agentmail_messages(inbox_id: str, limit: int = 20, labels: Optional[str] = None):
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            params = {"limit": limit}
            if labels:
                params["labels"] = labels
            resp = await http.get(
                f"{AGENTMAIL_BASE_URL}/inboxes/{inbox_id}/messages",
                headers=AGENTMAIL_HEADERS, params=params
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="AgentMail API error")
            data = resp.json()
            messages = []
            for msg in data.get("messages", []):
                messages.append({
                    "message_id": msg.get("message_id", ""),
                    "thread_id": msg.get("thread_id", ""),
                    "subject": msg.get("subject", "(no subject)"),
                    "from": msg.get("from_", msg.get("from", "")),
                    "to": msg.get("to", []),
                    "text": msg.get("extracted_text") or msg.get("text") or msg.get("preview", ""),
                    "html": msg.get("extracted_html") or msg.get("html", ""),
                    "created_at": msg.get("created_at", ""),
                    "labels": msg.get("labels", []),
                })
            return {"messages": messages, "count": data.get("count", len(messages)), "inbox_id": inbox_id}
    except httpx.HTTPError as e:
        logger.error(f"AgentMail messages error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch messages")


@router.post("/agentmail/inboxes/{inbox_id}/messages/{message_id}/labels")
async def update_message_labels(inbox_id: str, message_id: str, body: LabelUpdate):
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            payload = {}
            if body.add_labels:
                payload["add_labels"] = body.add_labels
            if body.remove_labels:
                payload["remove_labels"] = body.remove_labels
            resp = await http.patch(
                f"{AGENTMAIL_BASE_URL}/inboxes/{inbox_id}/messages/{message_id}",
                headers=AGENTMAIL_HEADERS, json=payload
            )
            if resp.status_code != 200:
                return {"status": "label_update_attempted", "note": "Labels may not be supported for this message"}
            return {"status": "updated", "message_id": message_id}
    except Exception as e:
        logger.warning(f"Label update failed: {e}")
        return {"status": "label_update_attempted", "note": str(e)}


@router.get("/agentmail/threads/{thread_id}")
async def get_agentmail_thread(thread_id: str):
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(f"{AGENTMAIL_BASE_URL}/threads/{thread_id}", headers=AGENTMAIL_HEADERS)
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="AgentMail API error")
            data = resp.json()
            messages = []
            for msg in data.get("messages", []):
                messages.append({
                    "message_id": msg.get("message_id", ""),
                    "subject": msg.get("subject", ""),
                    "from": msg.get("from_", msg.get("from", "")),
                    "to": msg.get("to", []),
                    "text": msg.get("extracted_text") or msg.get("text") or "",
                    "html": msg.get("extracted_html") or msg.get("html", ""),
                    "created_at": msg.get("created_at", ""),
                    "labels": msg.get("labels", []),
                })
            return {
                "thread_id": thread_id,
                "inbox_id": data.get("inbox_id", ""),
                "subject": data.get("subject", ""),
                "message_count": data.get("message_count", len(messages)),
                "messages": messages,
                "senders": data.get("senders", []),
                "recipients": data.get("recipients", []),
            }
    except httpx.HTTPError as e:
        logger.error(f"AgentMail thread error: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch thread")


@router.post("/agentmail/compose")
async def compose_email(body: ComposeEmail):
    try:
        payload = {"to": body.to, "subject": body.subject, "text": body.text}
        if body.html:
            payload["html"] = body.html
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.post(
                f"{AGENTMAIL_BASE_URL}/inboxes/{body.inbox_id}/messages/send",
                headers=AGENTMAIL_HEADERS, json=payload
            )
            if resp.status_code not in (200, 201):
                logger.error(f"AgentMail compose failed: {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=f"AgentMail error: {resp.text}")
            result = resp.json()
        brand = resolve_inbox_brand(body.inbox_id)
        entry = ActivityEntry(
            brand=brand, type="email_out",
            text=f"Email sent: {body.subject}",
            detail=f"To: {', '.join(body.to)} via {body.inbox_id}",
            time=now_iso()
        )
        await db.activity.insert_one(entry.model_dump())
        return {"status": "sent", "message_id": result.get("message_id", ""), "thread_id": result.get("thread_id", "")}
    except httpx.HTTPError as e:
        logger.error(f"Compose error: {e}")
        raise HTTPException(status_code=502, detail="Failed to send email")


@router.post("/agentmail/reply/{inbox_id}/{message_id}")
async def reply_to_message(inbox_id: str, message_id: str, body: ReplyEmail):
    try:
        payload = {"text": body.text}
        if body.html:
            payload["html"] = body.html
        async with httpx.AsyncClient(timeout=15) as http:
            resp = await http.post(
                f"{AGENTMAIL_BASE_URL}/inboxes/{inbox_id}/messages/{message_id}/reply",
                headers=AGENTMAIL_HEADERS, json=payload
            )
            if resp.status_code not in (200, 201):
                logger.error(f"AgentMail reply failed: {resp.text}")
                raise HTTPException(status_code=resp.status_code, detail=f"AgentMail error: {resp.text}")
            result = resp.json()
        brand = resolve_inbox_brand(inbox_id)
        entry = ActivityEntry(
            brand=brand, type="email_out",
            text=f"Reply sent from {inbox_id}",
            detail=body.text[:100], time=now_iso()
        )
        await db.activity.insert_one(entry.model_dump())
        return {"status": "sent", "message_id": result.get("message_id", ""), "thread_id": result.get("thread_id", "")}
    except httpx.HTTPError as e:
        logger.error(f"Reply error: {e}")
        raise HTTPException(status_code=502, detail="Failed to send reply")


# Webhooks

@router.post("/webhooks/agentmail")
async def agentmail_webhook(request: Request):
    try:
        payload = await request.json()
        event_type = payload.get("event_type", "unknown")
        message = payload.get("message", {})
        inbox_id = message.get("inbox_id", "")
        brand = resolve_inbox_brand(inbox_id)
        subject = message.get("subject", "")
        from_addr = message.get("from_", [""])[0] if isinstance(message.get("from_"), list) else message.get("from_", "")
        preview = message.get("preview", "")

        type_labels = {
            "message.received": "email_in", "message.sent": "email_out",
            "message.delivered": "system", "message.bounced": "error",
            "message.complained": "error", "message.rejected": "error",
        }
        type_texts = {
            "message.received": f"New email received: {subject}",
            "message.sent": f"Email sent: {subject}",
            "message.delivered": f"Email delivered: {subject}",
            "message.bounced": f"Email bounced: {subject}",
            "message.complained": f"Spam complaint: {subject}",
            "message.rejected": f"Email rejected: {subject}",
        }

        entry = ActivityEntry(
            brand=brand,
            type=type_labels.get(event_type, "system"),
            text=type_texts.get(event_type, f"{event_type}: {subject}"),
            detail=f"From: {from_addr}" if from_addr else preview[:100],
            time=now_iso()
        )
        await db.activity.insert_one(entry.model_dump())

        if event_type == "message.received" and inbox_id:
            await db.inboxes.update_one(
                {"email": inbox_id},
                {"$inc": {"pending_count": 1}, "$set": {"last_activity": now_iso()}},
                upsert=True
            )
            await ws_manager.broadcast("inbox_updated", {"inbox_id": inbox_id, "brand": brand})

        await ws_manager.broadcast("activity_log", {
            "type": type_labels.get(event_type, "system"),
            "text": type_texts.get(event_type, f"{event_type}: {subject}"),
            "brand": brand, "time": now_iso()
        })
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return {"status": "error", "detail": str(e)}


@router.post("/agentmail/webhooks/register")
async def register_agentmail_webhook():
    try:
        webhook_url = os.environ.get('REACT_APP_BACKEND_URL', '')
        if not webhook_url:
            return {"status": "error", "detail": "REACT_APP_BACKEND_URL not set"}
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.post(
                f"{AGENTMAIL_BASE_URL}/webhooks",
                headers=AGENTMAIL_HEADERS,
                json={
                    "url": f"{webhook_url}/api/v1/webhooks/agentmail",
                    "event_types": ["message.received", "message.sent", "message.delivered", "message.bounced"],
                }
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                await db.webhook_config.update_one(
                    {"provider": "agentmail"},
                    {"$set": {
                        "provider": "agentmail",
                        "webhook_id": data.get("webhook_id", ""),
                        "url": f"{webhook_url}/api/v1/webhooks/agentmail",
                        "created_at": now_iso(),
                    }},
                    upsert=True
                )
                return {"status": "registered", "webhook_id": data.get("webhook_id", ""), "url": f"{webhook_url}/api/v1/webhooks/agentmail"}
            else:
                return {"status": "error", "detail": resp.text}
    except Exception as e:
        logger.error(f"Webhook registration error: {e}")
        return {"status": "error", "detail": str(e)}


@router.get("/agentmail/webhooks")
async def list_agentmail_webhooks():
    try:
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.get(f"{AGENTMAIL_BASE_URL}/webhooks", headers=AGENTMAIL_HEADERS)
            if resp.status_code == 200:
                return resp.json()
            return {"webhooks": [], "error": resp.text}
    except Exception as e:
        return {"webhooks": [], "error": str(e)}


# Brand-map management

@router.get("/agentmail/brand-map")
async def get_brand_map():
    mappings = await db.inbox_brand_map.find({}, {"_id": 0}).to_list(100)
    if not mappings:
        return {"map": INBOX_BRAND_MAP, "source": "default"}
    return {"map": {m["domain"]: m["brand"] for m in mappings}, "source": "custom"}


@router.post("/agentmail/brand-map")
async def update_brand_map(mapping: dict):
    for domain, brand_slug in mapping.items():
        await db.inbox_brand_map.update_one(
            {"domain": domain},
            {"$set": {"domain": domain, "brand": brand_slug}},
            upsert=True
        )
        INBOX_BRAND_MAP[domain] = brand_slug
    return {"status": "updated", "map": INBOX_BRAND_MAP}
