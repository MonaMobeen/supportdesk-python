from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Jab client naya ticket banane ke liye data bheje
class TicketCreate(BaseModel):
    title: str
    description: str
    requester: str
    category: str
    priority: Optional[str] = "Medium"


# Jab server client ko ticket data wapas bheje
class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    requester: str
    category: str
    priority: str
    status: str
    assigned_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True   # SQLAlchemy object ko Pydantic mein convert karne deta hai