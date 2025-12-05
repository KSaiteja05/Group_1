from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class OrderResponse(BaseModel):
    order_id: str
    reservation_id: str
    user_id: str
    product_id: str
    quantity: int
    unit_price: float
    total_amount: float
    status: str
    payment_id: str
    created_at: datetime
    shipped_at: Optional[datetime] = None


class OrderStatusUpdate(BaseModel):
    status: str  # e.g. confirmed, shipped, cancelled
