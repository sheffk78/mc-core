from fastapi import APIRouter, HTTPException
from typing import Optional
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from db import db, ws_manager, now_iso
from models import ScheduleItem, ScheduleCreate, ScheduleEdit, ActivityEntry
from execution_history import enhance_schedule_item_with_execution_history, generate_weekly_schedule

router = APIRouter()

# Path to OpenClaw cron jobs registry
CRON_JOBS_PATH = Path.home() / ".openclaw" / "cron" / "jobs.json"


def read_cron_jobs():
    """Read cron jobs from ~/.openclaw/cron/jobs.json"""
    try:
        if CRON_JOBS_PATH.exists():
            with open(CRON_JOBS_PATH, 'r') as f:
                data = json.load(f)
                return data.get('jobs', [])
    except Exception as e:
        print(f"Error reading cron jobs: {e}")
    return []


async def convert_cron_job_to_schedule_item(job: dict) -> dict:
    """Convert OpenClaw cron job to schedule item format and enhance with history"""
    # Extract schedule expression
    schedule_info = job.get('schedule', {})
    
    if schedule_info.get('kind') == 'cron':
        cron_expr = schedule_info.get('expr', '')
    elif schedule_info.get('kind') == 'every':
        # Convert everyMs to a human-readable format
        every_ms = schedule_info.get('everyMs', 0)
        minutes = every_ms // 60000
        if minutes == 55:
            cron_expr = '*/55 * * * *'  # Every 55 minutes
        else:
            cron_expr = f'Every {minutes} minutes'
    else:
        cron_expr = 'Unknown'
    
    # Create schedule item
    item = {
        'id': job.get('id'),
        'name': job.get('name'),
        'description': job.get('description', ''),
        'cron': cron_expr,
        'enabled': job.get('enabled', True),
        'status': job.get('state', {}).get('lastStatus', 'scheduled'),
        'last_run': job.get('state', {}).get('lastRunAtMs'),
        'last_duration': job.get('state', {}).get('lastDurationMs'),
        'last_error': job.get('state', {}).get('lastError'),
        'created_at': now_iso(),
    }
    
    # Enhance with execution history from file
    enhanced = await enhance_schedule_item_with_execution_history(item)
    return enhanced


@router.get("/schedule")
async def get_schedule(brand: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0):
    """
    Get all cron jobs from ~/.openclaw/cron/jobs.json with execution history.
    Brand and status filters work on the converted schedule items.
    """
    # Read cron jobs from file
    cron_jobs = read_cron_jobs()
    
    # Convert to schedule items and enhance with history
    items = []
    for job in cron_jobs:
        try:
            item = await convert_cron_job_to_schedule_item(job)
            items.append(item)
        except Exception as e:
            print(f"Error converting job {job.get('id')}: {e}")
            continue
    
    # Apply filters
    if status:
        items = [i for i in items if i.get('status') == status]
    
    # Apply limit and offset
    items = items[offset:offset + limit]
    
    return items


@router.get("/schedule/weekly")
async def get_weekly_schedule(week_offset: int = 0):
    """
    Get the weekly calendar view for all cron jobs.
    week_offset: 0 = current week, -1 = last week, 1 = next week, etc.
    Returns weekStart, weekEnd (ISO date strings) and a flat list of events.
    """
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    monday = monday + timedelta(weeks=week_offset)
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=6)

    # Read from database instead of filesystem (for Railway compatibility)
    db_items = await db.schedule.find({"status": {"$ne": "inactive"}}, {"_id": 0}).to_list(None)
    
    # If database is empty, fall back to filesystem
    if not db_items:
        cron_jobs = read_cron_jobs()
    else:
        cron_jobs = db_items

    jobs = []
    for job in cron_jobs:
        try:
            # If it's already from DB, it has a different structure
            if 'cron' in job and 'id' in job:
                jobs.append(job)
            else:
                item = await convert_cron_job_to_schedule_item(job)
                jobs.append(item)
        except Exception as e:
            print(f"Error converting job {job.get('id')}: {e}")

    events = await generate_weekly_schedule(jobs, monday)

    return {
        "weekStart": monday.strftime("%Y-%m-%d"),
        "weekEnd": sunday.strftime("%Y-%m-%d"),
        "events": events,
    }


@router.get("/schedule/{job_id}")
async def get_schedule_item(job_id: str):
    item = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    
    # Enhance with execution history
    enhanced = await enhance_schedule_item_with_execution_history(item)
    return enhanced


@router.post("/schedule")
async def create_schedule_item(body: ScheduleCreate):
    item = ScheduleItem(
        brand=body.brand,
        name=body.name,
        description=body.description,
        cron=body.cron,
        agent_name=body.agent_name,
        created_at=now_iso(),
    )
    doc = item.model_dump()
    await db.schedule.insert_one(doc)
    doc.pop("_id", None)
    
    # Enhance with execution history
    doc = await enhance_schedule_item_with_execution_history(doc)
    
    entry = ActivityEntry(
        brand=body.brand, type="system",
        text=f"Schedule created: {body.name}",
        detail=f"Cron: {body.cron}", time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("schedule_updated", doc)
    return doc


@router.post("/schedule/{job_id}/pause")
async def pause_schedule(job_id: str):
    item = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    await db.schedule.update_one({"id": job_id}, {"$set": {"status": "paused"}})
    updated = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    
    # Enhance with execution history
    updated = await enhance_schedule_item_with_execution_history(updated)
    
    await ws_manager.broadcast("schedule_updated", updated)
    return {"status": "paused", "id": job_id}


@router.post("/schedule/{job_id}/resume")
async def resume_schedule(job_id: str):
    item = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    await db.schedule.update_one({"id": job_id}, {"$set": {"status": "active"}})
    updated = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    
    # Enhance with execution history
    updated = await enhance_schedule_item_with_execution_history(updated)
    
    await ws_manager.broadcast("schedule_updated", updated)
    return {"status": "active", "id": job_id}


@router.post("/schedule/{job_id}/run-now")
async def run_schedule_now(job_id: str):
    item = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    await db.schedule.update_one({"id": job_id}, {"$set": {"last_run": now_iso()}})
    entry = ActivityEntry(
        brand=item["brand"], type="system",
        text=f"Manual run triggered: {item['name']}",
        detail="", time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    updated = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    
    # Enhance with execution history
    updated = await enhance_schedule_item_with_execution_history(updated)
    
    await ws_manager.broadcast("schedule_updated", updated)
    return {"status": "running", "id": job_id}


@router.post("/schedule/{job_id}/edit")
async def edit_schedule(job_id: str, body: ScheduleEdit):
    item = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    updates = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.description is not None:
        updates["description"] = body.description
    if body.cron is not None:
        updates["cron"] = body.cron
    if updates:
        await db.schedule.update_one({"id": job_id}, {"$set": updates})
    updated = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    
    # Enhance with execution history
    updated = await enhance_schedule_item_with_execution_history(updated)
    
    return updated


@router.delete("/schedule/{job_id}")
async def delete_schedule_item(job_id: str):
    item = await db.schedule.find_one({"id": job_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Schedule item not found")
    await db.schedule.delete_one({"id": job_id})
    entry = ActivityEntry(
        brand=item["brand"], type="system",
        text=f"Schedule deleted: {item['name']}",
        detail="", time=now_iso()
    )
    await db.activity.insert_one(entry.model_dump())
    await ws_manager.broadcast("schedule_updated", {"id": job_id, "deleted": True})
    return {"status": "deleted", "id": job_id}
