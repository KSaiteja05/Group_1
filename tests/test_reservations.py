# tests/test_reservations.py
import pytest
import asyncio

from app.schemas.reservation_schema import ReservationCreate
from app.services import reservation_service as rs
from app.db import database as db_module
from pydantic import ValidationError


@pytest.mark.asyncio
async def test_reservation_creation_success():
    product_id = "PROD_TEST_1"
    await db_module.products_collection.insert_one({
        "product_id": product_id,
        "name": "Test Product",
        "description": "Test",
        "price": 100.0,
        "total_stock": 10,
        "available_stock": 10,
        "reserved_stock": 0,
    })

    payload = ReservationCreate(
        product_id=product_id,
        quantity=2,
        ttl_minutes=5,
    )
    user_email = "user1@test.com"

    res = await rs.create_reservation(payload, user_email)

    assert res.reservation_id.startswith("RES_")
    assert res.user_id == user_email
    assert res.product_id == product_id
    assert res.quantity == 2
    assert res.status == "active"

    product = await db_module.products_collection.find_one({"product_id": product_id})
    assert product["available_stock"] == 8
    assert product["reserved_stock"] == 2


@pytest.mark.asyncio
async def test_reservation_creation_insufficient_stock():
    product_id = "PROD_TEST_2"
    await db_module.products_collection.insert_one({
        "product_id": product_id,
        "name": "Test Product 2",
        "description": "Test",
        "price": 50.0,
        "total_stock": 1,
        "available_stock": 1,
        "reserved_stock": 0,
    })

    payload = ReservationCreate(
        product_id=product_id,
        quantity=5,
        ttl_minutes=5,
    )
    user_email = "user2@test.com"

    with pytest.raises(Exception) as exc:
        await rs.create_reservation(payload, user_email)

    assert "Insufficient stock" in str(exc.value)

    product = await db_module.products_collection.find_one({"product_id": product_id})
    assert product["available_stock"] == 1
    assert product["reserved_stock"] == 0


@pytest.mark.asyncio
async def test_concurrent_reservation_attempts():
    product_id = "PROD_TEST_3"
    await db_module.products_collection.insert_one({
        "product_id": product_id,
        "name": "Test Product 3",
        "description": "Test",
        "price": 10.0,
        "total_stock": 5,
        "available_stock": 5,
        "reserved_stock": 0,
    })

    user_email = "user3@test.com"

    payload1 = ReservationCreate(product_id=product_id, quantity=4, ttl_minutes=5)
    payload2 = ReservationCreate(product_id=product_id, quantity=4, ttl_minutes=5)

    async def try_reserve(payload):
        try:
            return await rs.create_reservation(payload, user_email)
        except Exception:
            return None

    res1, res2 = await asyncio.gather(
        try_reserve(payload1),
        try_reserve(payload2),
    )

    successful = [r for r in (res1, res2) if r is not None]
    assert len(successful) == 1

    product = await db_module.products_collection.find_one({"product_id": product_id})
    assert product["available_stock"] == 1
    assert product["reserved_stock"] == 4


@pytest.mark.asyncio
async def test_reservation_invalid_quantity():
    product_id = "PROD_TEST_4"
    await db_module.products_collection.insert_one({
        "product_id": product_id,
        "name": "Test Product 4",
        "description": "Test",
        "price": 10.0,
        "total_stock": 10,
        "available_stock": 10,
        "reserved_stock": 0,
    })

    # Pydantic itself should reject this
    with pytest.raises(ValidationError):
        ReservationCreate(
            product_id=product_id,
            quantity=0,
            ttl_minutes=5,
        )
