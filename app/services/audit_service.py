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
    await audit_collection.insert_one(doc)
