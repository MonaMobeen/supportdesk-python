from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class TicketHistory(Base):
    __tablename__ = "ticket_history"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    field_changed = Column(String(50), nullable=False)
    old_value = Column(String(200), nullable=True)
    new_value = Column(String(200), nullable=True)
    changed_at = Column(DateTime(timezone=True), server_default=func.now())