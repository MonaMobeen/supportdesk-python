from pydantic import BaseModel
from datetime import datetime


class CommentCreate(BaseModel):
    author: str
    text: str


class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    author: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True