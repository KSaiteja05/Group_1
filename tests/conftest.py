# tests/conftest.py

import pytest,pytest_asyncio
from types import SimpleNamespace
from typing import Any, Dict, List

from app.db import database as db_module
from app.services import reservation_service as rs


# ---------- Simple in-memory fake DB layer for tests ----------

class FakeInsertOneResult:
    def __init__(self, inserted_id: Any = None):
        self.inserted_id = inserted_id


class FakeUpdateResult:
    def __init__(self, matched_count: int = 0, modified_count: int = 0):
        self.matched_count = matched_count
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs: List[Dict]):
        self._docs = [d.copy() for d in docs]

    def sort(self, *args, **kwargs):
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length: int):
        return self._docs[:length]


class FakeCollection:
    """
    In-memory mini "Mongo collection" with just what we need:
      - insert_one
      - find_one
      - find_one_and_update
      - update_one
      - delete_many
      - find
      - count_documents
    """

    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    async def insert_one(self, doc: Dict[str, Any]):
        self.docs.append(doc.copy())
        return FakeInsertOneResult()

    async def find_one(self, filter: Dict[str, Any]):
        for d in self.docs:
            if _matches_filter(d, filter):
                return d.copy()
        return None

    async def find_one_and_update(
        self,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        return_document=None,
    ):
        for d in self.docs:
            if _matches_filter(d, filter):
                _apply_update(d, update)
                return d.copy()
        return None

    async def update_one(self, filter: Dict[str, Any], update: Dict[str, Any]):
        for d in self.docs:
            if _matches_filter(d, filter):
                _apply_update(d, update)
                return FakeUpdateResult(matched_count=1, modified_count=1)
        return FakeUpdateResult(matched_count=0, modified_count=0)

    async def delete_many(self, filter: Dict[str, Any]):
        if not filter:
            self.docs.clear()
            return
        remaining = []
        for d in self.docs:
            if not _matches_filter(d, filter):
                remaining.append(d)
        self.docs = remaining

    def find(self, filter: Dict[str, Any]):
        matched = [d for d in self.docs if _matches_filter(d, filter)]
        return FakeCursor(matched)

    async def count_documents(self, filter: Dict[str, Any]):
        return sum(1 for d in self.docs if _matches_filter(d, filter))


def _matches_filter(doc: Dict[str, Any], flt: Dict[str, Any]) -> bool:
    """
    Very tiny filter support:
      { field: value }
      { field: { "$gte": value } }
    """
    for key, cond in flt.items():
        if isinstance(cond, dict):
            if "$gte" in cond:
                if doc.get(key, None) < cond["$gte"]:
                    return False
            else:
                return False
        else:
            if doc.get(key, None) != cond:
                return False
    return True


def _apply_update(doc: Dict[str, Any], update: Dict[str, Any]):
    """
    Support for:
      { "$inc": { field: value } }
      { "$set": { field: value } }
    """
    for op, changes in update.items():
        if op == "$inc":
            for field, delta in changes.items():
                doc[field] = doc.get(field, 0) + delta
        elif op == "$set":
            for field, value in changes.items():
                doc[field] = value
        else:
            pass


# ---------- Pytest fixture wiring fake DB into the app ----------

@pytest.fixture(autouse=True)
def fake_db():
    """
    Runs before every test (sync fixture):
      - Creates fresh FakeCollection objects
      - Patches BOTH:
          app.db.database.*  AND
          app.services.reservation_service.*
      - Clears in-memory reservation_store
    """

    # 1️⃣ Fresh fake collections
    products = FakeCollection()
    reservations = FakeCollection()
    orders = FakeCollection()
    audits = FakeCollection()
    stock_history = FakeCollection()
    users = FakeCollection()

    # 2️⃣ Patch db_module (what routes/services normally import)
    db_module.products_collection = products
    db_module.reservations_collection = reservations
    db_module.orders_collection = orders
    db_module.audit_collection = audits
    db_module.stock_history_collection = stock_history
    db_module.users_collection = users
    db_module.db = SimpleNamespace(
        products=products,
        reservations=reservations,
        orders=orders,
        audit_logs=audits,
        stock_history=stock_history,
        users=users,
    )

    # 3️⃣ Patch reservation_service's own imported collections
    rs.products_collection = products
    rs.reservations_collection = reservations
    rs.orders_collection = orders

    # 4️⃣ Clear in-memory reservation store
    rs.reservation_store.clear()

    yield
    # No explicit cleanup needed; new fakes created next test


