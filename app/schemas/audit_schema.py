from datetime import datetime
from pydantic import BaseModel
from typing import Any, Optional, Dict


class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    entity_type: str
    entity_id: str
    user_id: Optional[str] = None
    changes: Dict[str, Any]
    timestamp: datetime
