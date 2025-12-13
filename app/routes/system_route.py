from fastapi import APIRouter, Depends

from app.db.database import db, products_collection, orders_collection, audit_collection
from app.services.reservation_service import reservation_store
from app.auth.deps import require_admin

router = APIRouter(tags=["System"])


@router.get("/health")
async def health():
    await db.command("ping")
    return {"status": "ok"}


@router.get("/metrics", dependencies=[Depends(require_admin)])
async def metrics():
    product_count = await products_collection.count_documents({})
    order_count = await orders_collection.count_documents({})
    active_reservations = len(reservation_store)
    return {
        "products": product_count,
        "orders": order_count,
        "active_reservations_in_memory": active_reservations,
    }


@router.get("/audit/", dependencies=[Depends(require_admin)])
async def get_audit_logs(limit: int = 50):
    cursor = audit_collection.find({}).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs
