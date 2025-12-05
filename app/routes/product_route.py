from fastapi import APIRouter, HTTPException
from typing import List
from uuid import uuid4

from app.db.database import products_collection, stock_history_collection
from app.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    StockAdjustmentRequest,
)
from app.utils.time_utils import now_utc
from pymongo import ReturnDocument

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse)
async def create_product(payload: ProductCreate):
    product_id = f"PROD_{uuid4().hex[:8]}"
    doc = {
        "product_id": product_id,
        "name": payload.name,
        "description": payload.description,
        "price": payload.price,
        "total_stock": payload.total_stock,
        "available_stock": payload.total_stock,
        "reserved_stock": 0,
        "created_at": now_utc(),
    }
    await products_collection.insert_one(doc)
    return ProductResponse(**doc)


@router.get("/", response_model=List[ProductResponse])
async def list_products():
    docs = await products_collection.find({}).to_list(length=1000)
    return [ProductResponse(**d) for d in docs]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    doc = await products_collection.find_one({"product_id": product_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(**doc)


@router.put("/{product_id}/stock", response_model=ProductResponse)
async def adjust_stock(product_id: str, payload: StockAdjustmentRequest):
    before = await products_collection.find_one({"product_id": product_id})
    if not before:
        raise HTTPException(status_code=404, detail="Product not found")

    updated = await products_collection.find_one_and_update(
        {"product_id": product_id},
        {
            "$inc": {
                "total_stock": payload.delta,
                "available_stock": payload.delta,
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    await stock_history_collection.insert_one(
        {
            "product_id": product_id,
            "delta": payload.delta,
            "reason": payload.reason,
            "timestamp": now_utc(),
            "before": {
                "total_stock": before["total_stock"],
                "available_stock": before["available_stock"],
            },
            "after": {
                "total_stock": updated["total_stock"],
                "available_stock": updated["available_stock"],
            },
        }
    )

    return ProductResponse(**updated)


@router.get("/{product_id}/history")
async def get_stock_history(product_id: str):
    cursor = stock_history_collection.find({"product_id": product_id}).sort(
        "timestamp", -1
    )
    docs = await cursor.to_list(length=200)

    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]

    return docs
