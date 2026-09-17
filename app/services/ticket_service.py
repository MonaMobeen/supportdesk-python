from sqlalchemy.orm import Session
from app.schemas.ticket import TicketUpdate
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

def get_all_tickets(db: Session):
    return db.query(Ticket).all()


def get_ticket_by_id(db: Session, ticket_id: int):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()



def update_ticket(db: Session, ticket_id: int, ticket_data: TicketUpdate):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        return None

    # Business Rule: Closed ticket edit nahi ho sakta
    if ticket.status == "Closed":
        raise ValueError("Cannot edit a closed ticket")

    update_data = ticket_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket