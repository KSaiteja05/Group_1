import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from main import app
from app.db import database as db_module
from app.auth.auth_handler import sign_jwt


@pytest_asyncio.fixture
async def admin_headers():
    admin_email = "admin@test.com"

    await db_module.users_collection.insert_one({
        "email": admin_email,
        "role": "admin"
    })

    token_data = sign_jwt(admin_email, role="admin")
    access_token = token_data["access_token"]

    return {
        "Authorization": f"Bearer {access_token}"
    }


@pytest.mark.asyncio
async def test_health_api():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# @pytest.mark.asyncio
# async def test_metrics_api_admin_access(admin_headers):
#     await db_module.products_collection.insert_one({
#         "product_id": "MET_PROD_1",
#         "name": "Metrics Product",
#         "description": "Metrics Test",
#         "price": 10.0,
#         "total_stock": 10,
#         "available_stock": 10,
#         "reserved_stock": 0,
#     })

#     transport = ASGITransport(app=app)

#     async with AsyncClient(transport=transport, base_url="http://test") as client:
#         response = await client.get(
#             "/metrics",
#             headers=admin_headers
#         )

#     assert response.status_code == 200

#     data = response.json()
#     assert "products" in data
#     assert "orders" in data
#     assert "active_reservations_in_memory" in data


@pytest.mark.asyncio
async def test_metrics_api_unauthorized():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 403


# @pytest.mark.asyncio
# async def test_audit_logs_admin_access(admin_headers):
#     transport = ASGITransport(app=app)

#     async with AsyncClient(transport=transport, base_url="http://test") as client:
#         response = await client.get(
#             "/audit/",
#             headers=admin_headers
#         )

#     assert response.status_code == 200
#     assert isinstance(response.json(), list)


