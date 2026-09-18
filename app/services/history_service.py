from sqlalchemy.orm import Session
from app.models.history import TicketHistory


def log_change(db: Session, ticket_id: int, field: str, old_value, new_value):
    record = TicketHistory(
        ticket_id=ticket_id,
        field_changed=field,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
    )
    db.add(record)


def get_history_by_ticket(db: Session, ticket_id: int):
    return (
        db.query(TicketHistory)
        .filter(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.changed_at.asc())
        .all()
    )