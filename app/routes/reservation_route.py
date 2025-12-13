from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.schemas.reservation_schema import (
    ReservationCreate,
    ReservationResponse,
    ReservationCommitRequest,
    CancelReservationRequest,
)
from app.schemas.order_schema import OrderResponse
from app.services import reservation_service as rs
from app.auth.deps import require_user
from app.db.database import products_collection

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("/", response_model=ReservationResponse)
async def create_reservation(
    payload: ReservationCreate,
    current_user: dict = Depends(require_user),
):
    user_email = current_user["email"]

    res = await rs.create_reservation(payload, user_email)

    product_doc = await products_collection.find_one(
        {"product_id": res.product_id},
        {"available_stock": 1, "_id": 0},
    )
    available_stock = product_doc["available_stock"] if product_doc else None

    return ReservationResponse(
        reservation_id=res.reservation_id,
        user_id=res.user_id,
        product_id=res.product_id,
        quantity=res.quantity,
        status=res.status,
        created_at=res.created_at,
        expires_at=res.expires_at,
        available_stock=available_stock,
    )


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: str,
    current_user: dict = Depends(require_user),
):
    res = await rs.get_reservation(reservation_id)

    # Ensure users can only see their own reservations
    if res.user_id != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not allowed to view this reservation")

    return ReservationResponse(
        reservation_id=res.reservation_id,
        user_id=res.user_id,
        product_id=res.product_id,
        quantity=res.quantity,
        status=res.status,
        created_at=res.created_at,
        expires_at=res.expires_at,
    )


@router.get("/user/{user_id}", response_model=List[ReservationResponse])
async def get_user_reservations(
    user_id: str,
    current_user: dict = Depends(require_user),
):
    user_email = current_user["email"]

    # 👇 use user_email instead of user_id
    items = await rs.get_user_active_reservations(user_email)

    return [
        ReservationResponse(
            reservation_id=r.reservation_id,
            user_id=r.user_id,
            product_id=r.product_id,
            quantity=r.quantity,
            status=r.status,
            created_at=r.created_at,
            expires_at=r.expires_at,
        )
        for r in items
    ]


@router.post("/{reservation_id}/commit", response_model=OrderResponse)
async def commit_reservation(
    reservation_id: str,
    payload: ReservationCommitRequest,
    current_user: dict = Depends(require_user),
):
    doc = await rs.commit_reservation(reservation_id, payload)

    if doc["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not allowed to commit this reservation")

    return OrderResponse(
        order_id=doc["order_id"],
        reservation_id=doc["reservation_id"],
        user_id=doc["user_id"],
        product_id=doc["product_id"],
        quantity=doc["quantity"],
        unit_price=doc["unit_price"],
        total_amount=doc["total_amount"],
        status=doc["status"],
        payment_id=doc["payment_id"],
        created_at=doc["created_at"],
        shipped_at=doc.get("shipped_at"),
    )


@router.post("/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: str,
    payload: CancelReservationRequest,
    current_user: dict = Depends(require_user),
):
    await rs.cancel_reservation(reservation_id, payload)
    return {"status": "cancelled", "reservation_id": reservation_id}
