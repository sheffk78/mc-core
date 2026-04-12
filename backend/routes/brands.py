from fastapi import APIRouter, HTTPException

from db import db
from models import Brand, BrandCreate, BrandUpdate

router = APIRouter()


@router.get("/brands")
async def get_brands():
    brands = await db.brands.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return brands


@router.post("/brands")
async def create_brand(body: BrandCreate):
    existing = await db.brands.find_one({"slug": body.slug}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Brand slug already exists")
    order = await db.brands.count_documents({})
    brand = Brand(name=body.name, slug=body.slug, color=body.color, order=order)
    doc = brand.model_dump()
    await db.brands.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.patch("/brands/{slug}")
async def update_brand(slug: str, body: BrandUpdate):
    brand = await db.brands.find_one({"slug": slug}, {"_id": 0})
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    updates = {}
    for field in ["name", "color", "active"]:
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = val
    if updates:
        await db.brands.update_one({"slug": slug}, {"$set": updates})
    updated = await db.brands.find_one({"slug": slug}, {"_id": 0})
    return updated


@router.delete("/brands/{slug}")
async def delete_brand(slug: str):
    if slug == "all":
        raise HTTPException(status_code=400, detail="Cannot delete 'All Brands'")
    result = await db.brands.delete_one({"slug": slug})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Brand not found")
    return {"status": "deleted", "slug": slug}
