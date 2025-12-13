from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.schemas.order_schema import OrderResponse, OrderStatusUpdate
from app.services import order_service as os
from app.auth.deps import get_current_user, require_admin  # 👈 NEW

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderResponse])
async def list_orders(current_user: dict = Depends(get_current_user)):
    # Normal user: only their orders
    # Admin: can see all orders
    if current_user["role"] == "admin":
        docs = await os.list_orders(user_id=None)
    else:
        docs = await os.list_orders(user_id=current_user["email"])

    return [OrderResponse(**d) for d in docs]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    doc = await os.get_order(order_id)

    # User can only view their own order, admin can view any
    if current_user["role"] != "admin" and doc["user_id"] != current_user["email"]:
        raise HTTPException(status_code=403, detail="Not allowed to view this order")

    return OrderResponse(**doc)


@router.put(
    "/{order_id}/status",
    response_model=OrderResponse,
    dependencies=[Depends(require_admin)],
)
async def update_order_status(order_id: str, payload: OrderStatusUpdate):
    doc = await os.update_order_status(order_id, payload.status)
    return OrderResponse(**doc)
