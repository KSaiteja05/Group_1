
import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    auth_route,
    product_route,
    reservation_route,
    order_route,
    system_route,
)
from app.services.reservation_service import expiration_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    task = asyncio.create_task(expiration_worker())
    try:
        yield
    finally:
        # Shutdown logic (optional but safe)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="Inventory Reservation & Order Locking Service",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_route.router)
app.include_router(product_route.router)
app.include_router(reservation_route.router)
app.include_router(order_route.router)
app.include_router(system_route.router)

