from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from pymongo import ReturnDocument

from app.db.database import orders_collection
from app.services.audit_service import log_event


async def list_orders(user_id: Optional[str] = None) -> List[dict]:
    query: Dict[str, Any] = {}
    if user_id:
        query["user_id"] = user_id
    cursor = orders_collection.find(query).sort("created_at", -1)
    return await cursor.to_list(length=200)


async def get_order(order_id: str) -> dict:
    doc = await orders_collection.find_one({"order_id": order_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Order not found")
    return doc


async def update_order_status(order_id: str, status: str) -> dict:
    updated = await orders_collection.find_one_and_update(
        {"order_id": order_id},
        {"$set": {"status": status}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Order not found")

    await log_event(
        "order_status_updated",
        "order",
        order_id,
        None,
        {"status": status},
    )

    return updated
