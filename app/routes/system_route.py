from fastapi import APIRouter

from app.db.database import audit_collection

router = APIRouter(tags=["System"]) 


@router.get("/audit/")
async def get_audit_logs(limit: int = 50):
    cursor = audit_collection.find({}).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs
