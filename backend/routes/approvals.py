from fastapi import APIRouter, HTTPException
from typing import Optional
import re
import httpx

from db import (
    db, ws_manager, now_iso, logger,
    AGENTMAIL_API_KEY, AGENTMAIL_BASE_URL, AGENTMAIL_HEADERS,
    get_send_inbox,
)
from models import (
    ApprovalItem, ApprovalDraftUpdate, EditApproveBody, ActivityEntry,
)

router = APIRouter()


@router.get("/approvals")
async def get_approvals(brand: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None):
    query = {}
    if brand and brand != "all":
        query["brand"] = brand
    if status:
        query["status"] = status
    else:
        query["status"] = "pending"
    if search and search.strip():
        search_regex = {"$regex": re.escape(search.strip()), "$options": "i"}
        query["$or"] = [
            {"subject": search_regex},
            {"preview": search_regex},
            {"from_address": search_regex},
            {"to_address": search_regex},
            {"agent_name": search_regex},
        ]
    items = await db.approvals.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)

    task_query = {"status": "approval"}
    if brand and brand != "all":
        task_query["brand"] = brand
    if search and search.strip():
        search_regex = {"$regex": re.escape(search.strip()), "$options": "i"}
        task_query["$or"] = [
            {"title": search_regex},
            {"description": search_regex},
            {"agent_note": search_regex},
        ]
    approval_tasks = await db.tasks.find(task_query, {"_id": 0}).sort("created_at", -1).to_list(50)
    for t in approval_tasks:
        items.append({
            "id": t["id"],
            "brand": t["brand"],
            "type": "task_approval",
            "agent_name": "Kit",
            "from_address": "",
            "to_address": "",
            "inbox": "",
            "subject": t.get("title", ""),
            "preview": t.get("description", "") or t.get("agent_note", ""),
            "description": t.get("description", ""),
            "agent_note": t.get("agent_note", ""),
            "created_at": t.get("created_at", ""),
            "status": "pending",
            "due_date": t.get("due_date", ""),
            "priority": t.get("priority", "normal"),
            "source": "task",
        })
    return items


@router.get("/approvals/{item_id}")
async def get_approval(item_id: str):
    item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Approval item not found")
    return item


@router.post("/approvals/{item_id}/approve")
async def approve_item(item_id: str):
    item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Approval item not found")

    send_inbox = item.get("from_address") or get_send_inbox(item.get("brand", ""))
    to_address = item.get("to_address", "")
    subject = item.get("subject", "")
    body_text = item.get("preview", "")

    send_result = None
    if to_address and AGENTMAIL_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                resp = await http.post(
                    f"{AGENTMAIL_BASE_URL}/inboxes/{send_inbox}/messages/send",
                    headers=AGENTMAIL_HEADERS,
                    json={"to": [to_address], "subject": subject, "text": body_text}
                )
                if resp.status_code in (200, 201):
                    send_result = resp.json()
                    logger.info(f"Email sent via AgentMail: {subject} -> {to_address}")
                else:
                    logger.warning(f"AgentMail send failed ({resp.status_code}): {resp.text}")
                    send_result = {"error": resp.text, "status_code": resp.status_code}
        except Exception as e:
            logger.error(f"AgentMail send error: {e}")
            send_result = {"error": str(e)}

    await db.approvals.update_one({"id": item_id}, {"$set": {"status": "approved"}})

    sent_detail = f"Sent to {to_address} via {send_inbox}" if to_address else f"Approved via {item.get('inbox', '')}"
    entry = ActivityEntry(
        brand=item["brand"],
        type="email_out" if send_result and "error" not in send_result else "approval",
        text=f"Approved & sent: {subject}",
        detail=sent_detail,
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    updated_item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    await ws_manager.broadcast("approval_updated", updated_item or {"id": item_id, "status": "approved"})
    await ws_manager.broadcast("activity_log", {
        "type": "email_out" if send_result and "error" not in send_result else "approval",
        "text": f"Approved & sent: {subject}", "brand": item["brand"], "time": now_iso()
    })
    return {
        "status": "approved",
        "id": item_id,
        "sent": send_result is not None and "error" not in (send_result or {}),
        "send_result": send_result,
    }


@router.patch("/approvals/{item_id}")
async def update_approval_draft(item_id: str, body: ApprovalDraftUpdate):
    item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Approval item not found")
    updates = {}
    if body.to_address is not None:
        updates["to_address"] = body.to_address
    if body.subject is not None:
        updates["subject"] = body.subject
    if body.preview is not None:
        updates["preview"] = body.preview
    if body.status is not None:
        valid_statuses = ("pending", "approved", "rejected", "discarded", "dismissed", "reviewed")
        if body.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        updates["status"] = body.status
    if updates:
        await db.approvals.update_one({"id": item_id}, {"$set": updates})
    updated = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    if body.status and body.status in ("dismissed", "discarded"):
        await ws_manager.broadcast("approval_updated", updated)
    return updated


@router.post("/approvals/{item_id}/reject")
async def reject_item(item_id: str):
    result = await db.approvals.find_one_and_update(
        {"id": item_id}, {"$set": {"status": "rejected"}}, projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Approval item not found")
    item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    entry = ActivityEntry(
        brand=item["brand"], type="approval",
        text=f"Rejected: {item['subject']}",
        detail="Sent back for revision", time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("approval_updated", item)
    await ws_manager.broadcast("activity_log", {
        "type": "approval", "text": f"Rejected: {item['subject']}", "brand": item["brand"], "time": now_iso()
    })
    return {"status": "rejected", "id": item_id}


@router.post("/approvals/{item_id}/discard")
async def discard_item(item_id: str):
    result = await db.approvals.find_one_and_update(
        {"id": item_id}, {"$set": {"status": "discarded"}}, projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Approval item not found")
    item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    entry = ActivityEntry(
        brand=item["brand"], type="approval",
        text=f"Discarded: {item['subject']}",
        detail="", time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("approval_updated", item)
    await ws_manager.broadcast("activity_log", {
        "type": "approval", "text": f"Discarded: {item['subject']}", "brand": item["brand"], "time": now_iso()
    })
    return {"status": "discarded", "id": item_id}


@router.post("/approvals/{item_id}/dismiss")
async def dismiss_item(item_id: str):
    return await discard_item(item_id)


@router.post("/approvals/{item_id}/edit-approve")
async def edit_approve_item(item_id: str, body: EditApproveBody):
    item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Approval item not found")

    updates = {}
    if body.subject is not None:
        updates["subject"] = body.subject
    if body.to_address is not None:
        updates["to_address"] = body.to_address
    if body.body is not None:
        updates["preview"] = body.body
    if updates:
        await db.approvals.update_one({"id": item_id}, {"$set": updates})
        item.update(updates)

    send_inbox = item.get("from_address") or get_send_inbox(item.get("brand", ""))
    to_address = item.get("to_address", "")
    subject = item.get("subject", "")
    body_text = item.get("preview", "")

    send_result = None
    if to_address and send_inbox:
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                response = await http.post(
                    f"{AGENTMAIL_BASE_URL}/inboxes/{send_inbox}/messages",
                    headers=AGENTMAIL_HEADERS,
                    json={
                        "to": [to_address] if isinstance(to_address, str) else to_address,
                        "subject": subject,
                        "text": body_text,
                    },
                )
                send_result = response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            send_result = {"error": str(e)}

    await db.approvals.update_one({"id": item_id}, {"$set": {"status": "approved"}})
    entry = ActivityEntry(
        brand=item["brand"], type="email_out",
        text=f"Approved (edited) & sent: {subject}",
        detail=f"To: {to_address} via {send_inbox}",
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    updated_item = await db.approvals.find_one({"id": item_id}, {"_id": 0})
    await ws_manager.broadcast("approval_updated", updated_item or {"id": item_id, "status": "approved"})
    await ws_manager.broadcast("activity_log", {
        "type": "email_out", "text": f"Approved (edited): {subject}", "brand": item["brand"], "time": now_iso()
    })
    return {
        "status": "approved",
        "id": item_id,
        "sent": send_result is not None and "error" not in (send_result or {}),
        "send_result": send_result,
    }
