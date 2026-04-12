from fastapi import APIRouter, HTTPException
from typing import Optional

from db import db, now_iso
from models import UserProfile, UserCreate, UserUpdate

router = APIRouter()


@router.get("/users")
async def get_users():
    users = await db.users.find({}, {"_id": 0}).sort("created_at", 1).to_list(50)
    return users


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users")
async def create_user(body: UserCreate):
    user = UserProfile(
        name=body.name,
        role=body.role,
        email=body.email,
        avatar_color=body.avatar_color,
        created_at=now_iso(),
    )
    doc = user.model_dump()
    await db.users.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.patch("/users/{user_id}")
async def update_user(user_id: str, body: UserUpdate):
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updates = {}
    for field in ["name", "role", "email", "avatar_color", "active"]:
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = val
    if updates:
        await db.users.update_one({"id": user_id}, {"$set": updates})
    updated = await db.users.find_one({"id": user_id}, {"_id": 0})
    return updated


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted", "id": user_id}


@router.get("/agents")
async def get_agents(brand: Optional[str] = None):
    query = {}
    if brand and brand != "all":
        query["brand"] = brand
    agents = await db.agents.find(query, {"_id": 0}).to_list(100)
    return agents
