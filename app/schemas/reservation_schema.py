from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReservationCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    ttl_minutes: int = Field(gt=0, le=60)


class ReservationResponse(BaseModel):
    reservation_id: str
    user_id: str
    product_id: str
    quantity: int
    status: str
    created_at: datetime
    expires_at: datetime
    available_stock: Optional[int] = None


class ReservationCommitRequest(BaseModel):
    payment_id: str
    shipping_address: str


class CancelReservationRequest(BaseModel):
    reason: str
