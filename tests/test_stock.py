# tests/test_stock.py
import pytest
import asyncio

from pymongo import ReturnDocument  # used only for the constant
from app.db import database as db_module


@pytest.mark.asyncio
async def test_atomic_stock_deduction():
    product_id = "PROD_STOCK_1"
    await db_module.products_collection.insert_one({
        "product_id": product_id,
        "name": "Stock Product",
        "description": "Stock test",
        "price": 20.0,
        "total_stock": 10,
        "available_stock": 10,
        "reserved_stock": 0,
    })

    updated = await db_module.products_collection.find_one_and_update(
        {"product_id": product_id, "available_stock": {"$gte": 3}},
        {"$inc": {"available_stock": -3}},
        return_document=ReturnDocument.AFTER,
    )

    assert updated is not None
    assert updated["available_stock"] == 7


@pytest.mark.asyncio
async def test_concurrent_stock_modifications():
    product_id = "PROD_STOCK_2"
    await db_module.products_collection.insert_one({
        "product_id": product_id,
        "name": "Stock Product 2",
        "description": "Stock test",
        "price": 30.0,
        "total_stock": 5,
        "available_stock": 5,
        "reserved_stock": 0,
    })

    async def dec_one():
        return await db_module.products_collection.find_one_and_update(
            {"product_id": product_id, "available_stock": {"$gte": 1}},
            {"$inc": {"available_stock": -1}},
            return_document=ReturnDocument.AFTER,
        )

    results = await asyncio.gather(*[dec_one() for _ in range(10)])
    success_count = sum(1 for r in results if r is not None)
    assert success_count == 5  # stock can't go below 0

    product = await db_module.products_collection.find_one({"product_id": product_id})
    assert product["available_stock"] == 0


@pytest.mark.asyncio
async def test_rollback_scenario_like_behavior():
    product_id = "PROD_STOCK_3"
    await db_module.products_collection.insert_one({
        "product_id": product_id,
        "name": "Rollback Product",
        "description": "Test",
        "price": 40.0,
        "total_stock": 10,
        "available_stock": 10,
        "reserved_stock": 0,
    })

    # simulate reserve
    await db_module.products_collection.update_one(
        {"product_id": product_id},
        {"$inc": {"available_stock": -2, "reserved_stock": 2}},
    )

    # simulate failure rollback
    await db_module.products_collection.update_one(
        {"product_id": product_id},
        {"$inc": {"available_stock": 2, "reserved_stock": -2}},
    )

    product = await db_module.products_collection.find_one({"product_id": product_id})
    assert product["available_stock"] == 10
    assert product["reserved_stock"] == 0
