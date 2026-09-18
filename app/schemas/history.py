from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HistoryResponse(BaseModel):
    id: int
    ticket_id: int
    field_changed: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    changed_at: datetime

    class Config:
        from_attributes = True