import asyncio
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.schemas.reservation_schema import ReservationCreate
from pymongo import ReturnDocument

from app.db.database import (
    products_collection,
    reservations_collection,
    orders_collection,
)
from app.services.audit_service import log_event
from app.utils.time_utils import now_utc


class ReservationInMemory(BaseModel):
    reservation_id: str
    user_id: str
    product_id: str
    quantity: int
    status: str
    created_at: datetime
    expires_at: datetime
    unit_price: float


reservation_store: Dict[str, ReservationInMemory] = {}
reservation_lock = asyncio.Lock()


async def create_reservation(payload: ReservationCreate, user_id: str) -> ReservationInMemory:
    async with reservation_lock:
        product = await products_collection.find_one_and_update(
            {
                "product_id": payload.product_id,
                "available_stock": {"$gte": payload.quantity},
            },
            {
                "$inc": {
                    "available_stock": -payload.quantity,
                    "reserved_stock": payload.quantity,
                }
            },
            return_document=ReturnDocument.AFTER,
        )

        if not product:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock or product not found",
            )

        reservation_id = f"RES_{uuid4().hex[:8]}"
        created_at = now_utc()
        expires_at = created_at + timedelta(minutes=payload.ttl_minutes)
        unit_price = float(product["price"])

        res = ReservationInMemory(
            reservation_id=reservation_id,
            user_id=user_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            status="active",
            created_at=created_at,
            expires_at=expires_at,
            unit_price=unit_price,
        )

        reservation_store[reservation_id] = res
        await reservations_collection.insert_one(res.model_dump())

        await log_event(
            "reservation_created",
            "reservation",
            reservation_id,
            user_id,
            {"product_id": payload.product_id, "quantity": payload.quantity},
        )

        return res


async def get_reservation(reservation_id: str) -> ReservationInMemory:
    async with reservation_lock:
        res = reservation_store.get(reservation_id)

    if res:
        return res

    doc = await reservations_collection.find_one({"reservation_id": reservation_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return ReservationInMemory(**doc)


async def get_user_active_reservations(user_id: str) -> List[ReservationInMemory]:
    async with reservation_lock:
        return [
            r
            for r in reservation_store.values()
            if r.user_id == user_id and r.status == "active"
        ]


async def _restore_stock_for_reservation(res: ReservationInMemory):
    await products_collection.update_one(
        {"product_id": res.product_id},
        {
            "$inc": {
                "reserved_stock": -res.quantity,
                "available_stock": res.quantity,
            }
        },
    )


async def commit_reservation(reservation_id: str, commit_payload) -> dict:
    async with reservation_lock:
        res = reservation_store.get(reservation_id)
        if not res:
            raise HTTPException(
                status_code=404, detail="Reservation not active or already processed"
            )

        if res.status != "active":
            raise HTTPException(status_code=400, detail="Reservation not active")

        if res.expires_at < now_utc():
            await _restore_stock_for_reservation(res)
            res.status = "expired"
            reservation_store.pop(reservation_id, None)
            await reservations_collection.update_one(
                {"reservation_id": reservation_id},
                {"$set": {"status": "expired"}},
            )
            await log_event(
                "reservation_expired_on_commit",
                "reservation",
                reservation_id,
                res.user_id,
            )
            raise HTTPException(status_code=400, detail="Reservation expired")

        order_id = f"ORD_{uuid4().hex[:8]}"
        total_amount = res.unit_price * res.quantity

        order_doc = {
            "order_id": order_id,
            "reservation_id": reservation_id,
            "user_id": res.user_id,
            "product_id": res.product_id,
            "quantity": res.quantity,
            "unit_price": res.unit_price,
            "total_amount": total_amount,
            "status": "confirmed",
            "payment_id": commit_payload.payment_id,
            "shipping_address": commit_payload.shipping_address,
            "created_at": now_utc(),
            "shipped_at": None,
        }
        await orders_collection.insert_one(order_doc)

        await products_collection.update_one(
            {"product_id": res.product_id},
            {
                "$inc": {
                    "reserved_stock": -res.quantity,
                    "total_stock": -res.quantity,
                }
            },
        )

        res.status = "committed"
        reservation_store.pop(reservation_id, None)
        await reservations_collection.update_one(
            {"reservation_id": reservation_id},
            {"$set": {"status": "committed"}},
        )

        await log_event(
            "order_committed",
            "order",
            order_id,
            res.user_id,
            {"reservation_id": reservation_id, "total_amount": total_amount},
        )

        return order_doc


async def cancel_reservation(reservation_id: str, cancel_payload):
    async with reservation_lock:
        res = reservation_store.get(reservation_id)
        if not res:
            raise HTTPException(
                status_code=404, detail="Reservation not active or already processed"
            )

        if res.status != "active":
            raise HTTPException(status_code=400, detail="Reservation not active")

        await _restore_stock_for_reservation(res)
        res.status = "cancelled"
        reservation_store.pop(reservation_id, None)

        await reservations_collection.update_one(
            {"reservation_id": reservation_id},
            {
                "$set": {
                    "status": "cancelled",
                    "cancel_reason": cancel_payload.reason,
                }
            },
        )

        await log_event(
            "reservation_cancelled",
            "reservation",
            reservation_id,
            res.user_id,
            {"reason": cancel_payload.reason},
        )


async def cleanup_expired_reservations():
    now = now_utc()
    to_expire: List[ReservationInMemory] = []

    async with reservation_lock:
        for res_id, res in list(reservation_store.items()):
            if res.status == "active" and res.expires_at < now:
                to_expire.append(res)
                reservation_store.pop(res_id, None)

    for res in to_expire:
        await _restore_stock_for_reservation(res)
        await reservations_collection.update_one(
            {"reservation_id": res.reservation_id},
            {"$set": {"status": "expired"}},
        )
        await log_event(
            "reservation_expired",
            "reservation",
            res.reservation_id,
            res.user_id,
            {"product_id": res.product_id, "quantity": res.quantity},
        )


async def expiration_worker():
    while True:
        await asyncio.sleep(30)
        await cleanup_expired_reservations()
