from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate


def create_ticket(db: Session, ticket_data: TicketCreate) -> Ticket:
    new_ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        requester=ticket_data.requester,
        category=ticket_data.category,
        priority=ticket_data.priority,
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket