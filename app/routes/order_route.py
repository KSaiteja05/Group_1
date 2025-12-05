from fastapi import APIRouter
from typing import List, Optional

from app.schemas.order_schema import OrderResponse, OrderStatusUpdate
from app.services import order_service as os

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/", response_model=List[OrderResponse])
async def list_orders(user_id: Optional[str] = None):
    docs = await os.list_orders(user_id=user_id)
    return [OrderResponse(**d) for d in docs]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    doc = await os.get_order(order_id)
    return OrderResponse(**doc)


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(order_id: str, payload: OrderStatusUpdate):
    doc = await os.update_order_status(order_id, payload.status)
    return OrderResponse(**doc)
