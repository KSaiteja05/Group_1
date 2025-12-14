from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    total_stock: int = Field(ge=0)


class ProductResponse(BaseModel):
    product_id: str
    name: str
    description: Optional[str] = None
    price: float
    total_stock: int
    available_stock: int
    reserved_stock: int
    created_at: Optional[datetime] = None


class StockAdjustmentRequest(BaseModel):
    change_quantity: int
    reason: str
