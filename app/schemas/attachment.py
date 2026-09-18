from pydantic import BaseModel
from datetime import datetime


class AttachmentResponse(BaseModel):
    id: int
    ticket_id: int
    filename: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime

    class Config:
        from_attributes = True