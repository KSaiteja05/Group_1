from typing import Optional, Dict, Any
from app.db.database import audit_collection
from app.utils.time_utils import now_utc


async def log_event(
    event_type: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
):
    doc = {
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "user_id": user_id,
        "changes": changes or {},
        "timestamp": now_utc(),
        "ip_address": None,
        "user_agent": None,
    }
    print(f"[AUDIT LOG] Writing to DB: {doc}")
    try:
        result = await audit_collection.insert_one(doc)
        print(f"[AUDIT LOG] Inserted with id: {result.inserted_id}")
    except Exception as e:
        print(f"[AUDIT LOG ERROR] {e}")
