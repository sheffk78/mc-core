from fastapi import APIRouter, HTTPException
from typing import Optional
import re

from db import db, ws_manager, now_iso
from models import (
    TaskItem, TaskCreate, TaskUpdate, TaskStatusUpdate,
    TaskDeferUpdate, TaskRedirectUpdate, ActivityEntry,
)

router = APIRouter()


@router.get("/tasks")
async def get_tasks(brand: Optional[str] = None, status: Optional[str] = None, assignee: Optional[str] = None, include_archived: bool = False):
    query = {}
    if brand and brand != "all":
        query["brand"] = brand
    if status:
        query["status"] = status
    elif not include_archived:
        query["status"] = {"$ne": "archived"}
    if assignee and assignee != "all":
        query["assignee"] = assignee
    tasks = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return tasks


@router.get("/tasks/{task_id}")
async def get_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/tasks")
async def create_task(task_input: TaskCreate):
    task = TaskItem(
        title=task_input.title,
        brand=task_input.brand,
        description=task_input.description or "",
        due_date=task_input.due_date or "",
        priority=task_input.priority or "normal",
        assignee=task_input.assignee or "",
        agent_note=task_input.agent_note or "",
        metadata=task_input.metadata,
        created_at=now_iso()
    )
    doc = task.model_dump()
    await db.tasks.insert_one(doc)
    doc.pop("_id", None)
    entry = ActivityEntry(
        brand=task_input.brand,
        type="task",
        text=f"New task created: {task_input.title}",
        detail=f"Priority: {task_input.priority or 'normal'}",
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("action_item_new", doc)
    await ws_manager.broadcast("activity_log", {
        "type": "task", "text": f"New task: {task_input.title}", "brand": task_input.brand, "time": now_iso()
    })
    return doc


@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, body: TaskUpdate):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updates = {}
    for field in ["title", "description", "due_date", "priority", "assignee", "agent_note", "user_note"]:
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = val
    # Handle metadata (merge with existing if present)
    if body.metadata is not None:
        existing_meta = task.get("metadata") or {}
        existing_meta.update(body.metadata)
        updates["metadata"] = existing_meta
    # Handle status change via PATCH
    if body.status is not None:
        valid = ("open", "in_progress", "approval", "completed")
        if body.status not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid)}")
        updates["status"] = body.status
        if body.status == "completed":
            updates["completed_at"] = now_iso()
        else:
            updates["completed_at"] = None
    # Handle append_agent_note (append to existing instead of replacing)
    if body.append_agent_note is not None:
        existing_note = task.get("agent_note", "")
        updates["agent_note"] = (existing_note + "\n\n" + body.append_agent_note).strip() if existing_note else body.append_agent_note
    if updates:
        await db.tasks.update_one({"id": task_id}, {"$set": updates})
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})

    # Auto-dismiss linked approval when task is completed
    if body.status == "completed":
        meta = updated.get("metadata") or {}
        approval_id = meta.get("approval_id")
        if approval_id:
            await db.approvals.update_one(
                {"id": approval_id},
                {"$set": {"status": "dismissed"}}
            )
            await ws_manager.broadcast("approval_updated", {"id": approval_id, "status": "dismissed"})

    await ws_manager.broadcast("action_item_updated", updated)
    return updated


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    result = await db.tasks.find_one_and_update(
        {"id": task_id},
        {"$set": {"status": "completed", "completed_at": now_iso()}},
        projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    entry = ActivityEntry(
        brand=task["brand"],
        type="task",
        text=f"Task completed: {task['title']}",
        detail="",
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())

    # Auto-dismiss linked approval
    meta = task.get("metadata") or {}
    approval_id = meta.get("approval_id")
    if approval_id:
        await db.approvals.update_one({"id": approval_id}, {"$set": {"status": "dismissed"}})
        await ws_manager.broadcast("approval_updated", {"id": approval_id, "status": "dismissed"})

    return {"status": "completed", "id": task_id}


@router.post("/tasks/{task_id}/reopen")
async def reopen_task(task_id: str):
    result = await db.tasks.find_one_and_update(
        {"id": task_id},
        {"$set": {"status": "open", "completed_at": None}},
        projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "open", "id": task_id}


@router.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, body: TaskStatusUpdate):
    if body.status not in ("open", "in_progress", "approval", "completed"):
        raise HTTPException(status_code=400, detail="Invalid status. Must be: open, in_progress, approval, completed")
    updates = {"status": body.status}
    if body.status == "completed":
        updates["completed_at"] = now_iso()
    elif body.status != "completed":
        updates["completed_at"] = None
    result = await db.tasks.find_one_and_update(
        {"id": task_id},
        {"$set": updates},
        projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    status_labels = {"open": "reopened", "in_progress": "moved to In Progress", "approval": "moved to Approval", "completed": "completed"}
    entry = ActivityEntry(
        brand=task["brand"],
        type="task",
        text=f"Task {status_labels.get(body.status, body.status)}: {task['title']}",
        detail="",
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("action_item_updated", task)
    await ws_manager.broadcast("activity_log", {
        "type": "task", "text": f"Task {status_labels.get(body.status, body.status)}: {task['title']}", "brand": task["brand"], "time": now_iso()
    })
    return {"status": body.status, "id": task_id}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.tasks.delete_one({"id": task_id})
    await db.approvals.delete_many({"id": task_id})
    entry = ActivityEntry(
        brand=task.get("brand", "all"),
        type="task",
        text=f"Task trashed: {task['title']}",
        detail="",
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("action_item_deleted", {"id": task_id})
    await ws_manager.broadcast("activity_log", {
        "type": "task", "text": f"Task trashed: {task['title']}", "brand": task.get("brand", "all"), "time": now_iso()
    })
    return {"status": "deleted", "id": task_id}


@router.post("/tasks/{task_id}/defer")
async def defer_task(task_id: str, body: TaskDeferUpdate):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updates = {"due_date": body.due_date, "status": "pending" if task.get("status") == "pending" else task.get("status", "open")}
    if body.reason:
        updates["user_note"] = body.reason
    await db.tasks.update_one({"id": task_id}, {"$set": updates})
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    entry = ActivityEntry(
        brand=task["brand"], type="task",
        text=f"Task deferred: {task['title']}",
        detail=f"New due: {body.due_date}" + (f" -- {body.reason}" if body.reason else ""),
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("action_item_updated", updated)
    return {"status": "deferred", "id": task_id}


@router.post("/tasks/{task_id}/redirect")
async def redirect_task(task_id: str, body: TaskRedirectUpdate):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updates = {"status": "open", "user_note": body.note}
    if body.priority:
        updates["priority"] = body.priority
    await db.tasks.update_one({"id": task_id}, {"$set": updates})
    updated = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    entry = ActivityEntry(
        brand=task["brand"], type="task",
        text=f"Task redirected to Kit: {task['title']}",
        detail=body.note[:100],
        time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("action_item_updated", updated)
    return {"status": "redirected", "id": task_id}


# Action Items (aliases)

@router.get("/action-items")
async def get_action_items(brand: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0):
    query = {}
    if brand and brand != "all":
        query["brand"] = brand
    if status:
        query["status"] = status
    items = await db.tasks.find(query, {"_id": 0}).sort("created_at", -1).skip(offset).to_list(limit)
    return items


@router.get("/action-items/{item_id}")
async def get_action_item(item_id: str):
    item = await db.tasks.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return item


@router.post("/action-items/{item_id}/complete")
async def complete_action_item(item_id: str):
    return await complete_task(item_id)


@router.post("/action-items/{item_id}/defer")
async def defer_action_item(item_id: str, body: TaskDeferUpdate):
    return await defer_task(item_id, body)


@router.post("/action-items/{item_id}/redirect")
async def redirect_action_item(item_id: str, body: TaskRedirectUpdate):
    return await redirect_task(item_id, body)
