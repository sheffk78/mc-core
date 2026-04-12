from fastapi import APIRouter, HTTPException

from db import db, now_iso
from models import EmailTemplate, EmailTemplateCreate

router = APIRouter()


@router.get("/templates")
async def list_templates():
    templates = await db.email_templates.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return templates


@router.post("/templates")
async def create_template(body: EmailTemplateCreate):
    template = EmailTemplate(
        name=body.name,
        subject=body.subject,
        body=body.body,
        created_at=now_iso(),
    )
    doc = template.model_dump()
    await db.email_templates.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str):
    result = await db.email_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "deleted", "id": template_id}
