from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import uuid4
from pymongo import ReturnDocument
from app.services.audit_service import log_event

from app.db.database import products_collection, stock_history_collection
from app.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    StockAdjustmentRequest,
)
from app.utils.time_utils import now_utc
from app.auth.deps import require_admin

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/", response_model=ProductResponse, dependencies=[Depends(require_admin)])
async def create_product(
    payload: ProductCreate,
    current_user: dict = Depends(require_admin),  
):
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

    await log_event(
        event_type="product_created",
        entity_type="product",
        entity_id=product_id,
        user_id=current_user["email"],
        changes={"new": {
            "name": payload.name,
            "price": payload.price,
            "total_stock": payload.total_stock,
        }},
    )

    return ProductResponse(**doc)


# ❌ public – no auth required
@router.get("/", response_model=List[ProductResponse])
async def list_products():
    docs = await products_collection.find({}).to_list(length=1000)
    return [ProductResponse(**d) for d in docs]


# ❌ public – no auth required
@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    doc = await products_collection.find_one({"product_id": product_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(**doc)


@router.put(
    "/{product_id}/stock",
    response_model=ProductResponse,
    dependencies=[Depends(require_admin)],
)
async def adjust_stock(
    product_id: str,
    payload: StockAdjustmentRequest,
    current_user: dict = Depends(require_admin),
):
    before = await products_collection.find_one({"product_id": product_id})
    if not before:
        raise HTTPException(status_code=404, detail="Product not found")

    updated = await products_collection.find_one_and_update(
        {"product_id": product_id},
        {
            "$inc": {
                "total_stock": payload.change_quantity,
                "available_stock": payload.change_quantity,
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    await stock_history_collection.insert_one(
        {
            "product_id": product_id,
            "change_quantity": payload.change_quantity,
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

    await log_event(
        event_type="stock_updated",
        entity_type="product",
        entity_id=product_id,
        user_id=current_user["email"],
        changes={
            "change_quantity": payload.change_quantity,
            "reason": payload.reason,
            "before": {
                "total_stock": before["total_stock"],
                "available_stock": before["available_stock"],
            },
            "after": {
                "total_stock": updated["total_stock"],
                "available_stock": updated["available_stock"],
            },
        },
    )

    return ProductResponse(**updated)


@router.get("/{product_id}/history", dependencies=[Depends(require_admin)])
async def get_stock_history(product_id: str,
    current_user: dict = Depends(require_admin),):
    cursor = stock_history_collection.find({"product_id": product_id}).sort(
        "timestamp", -1
    )
    history = await cursor.to_list(length=200)
    for h in history:
        if "_id" in h:
            h["_id"] = str(h["_id"])
    return history
