from sqlalchemy.orm import Session
from app.schemas.ticket import TicketUpdate
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate


# Valid status transitions define kar rahe hain
VALID_TRANSITIONS = {
    "Open": ["In Progress", "Closed"],
    "In Progress": ["Resolved", "Open"],
    "Resolved": ["Closed", "In Progress"],
    "Closed": ["Open"],  # sirf reopen ho sakta hai
}

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

    update_data = ticket_data.model_dump(exclude_unset=True)

    # Agar status change ho raha hai, to rules check karo
    if "status" in update_data:
        new_status = update_data["status"]
        current_status = ticket.status

        if new_status != current_status:
            allowed = VALID_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                raise ValueError(
                    f"Cannot change status from '{current_status}' to '{new_status}'"
                )

            # Business Rule: Closed karte waqt resolution note zaroori hai
            if new_status == "Closed" and not update_data.get("resolution_note") and not ticket.resolution_note:
                raise ValueError("Resolution note is required to close a ticket")

    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket