from sqlalchemy.orm import Session
from app.schemas.ticket import TicketUpdate
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate
from app.models.agent import Agent
from app.services import history_service
from typing import Optional
from datetime import datetime
from sqlalchemy import or_


VALID_TRANSITIONS = {
    "Open": ["In Progress", "Closed"],
    "In Progress": ["Resolved", "Open"],
    "Resolved": ["Closed", "In Progress"],
    "Closed": ["Open"],
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


def get_all_tickets(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    requester: Optional[str] = None,
    assigned_agent: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 20,
):
    query = db.query(Ticket)

    # Filters
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if category:
        query = query.filter(Ticket.category == category)
    if requester:
        query = query.filter(Ticket.requester == requester)
    if assigned_agent:
        query = query.filter(Ticket.assigned_agent == assigned_agent)
    if created_after:
        query = query.filter(Ticket.created_at >= created_after)
    if created_before:
        query = query.filter(Ticket.created_at <= created_before)

    # Search (title ya description mein text dhoondo)
    if search:
        query = query.filter(
            or_(
                Ticket.title.ilike(f"%{search}%"),
                Ticket.description.ilike(f"%{search}%"),
            )
        )

    # Sorting
    sort_column = getattr(Ticket, sort_by, Ticket.created_at)
    if order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination (bade result set ko control karna)
    total = query.count()
    tickets = query.offset(skip).limit(limit).all()

    return tickets, total

def get_ticket_by_id(db: Session, ticket_id: int):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()

def update_ticket(db: Session, ticket_id: int, ticket_data: TicketUpdate):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        return None

    update_data = ticket_data.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = update_data["status"]
        current_status = ticket.status

        if new_status != current_status:
            allowed = VALID_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                raise ValueError(
                    f"Cannot change status from '{current_status}' to '{new_status}'"
                )

            if new_status == "Closed" and not update_data.get("resolution_note") and not ticket.resolution_note:
                raise ValueError("Resolution note is required to close a ticket")

    if "assigned_agent" in update_data and update_data["assigned_agent"]:
        agent_exists = db.query(Agent).filter(
            Agent.name == update_data["assigned_agent"]
        ).first()
        if not agent_exists:
            raise ValueError(
                f"Agent '{update_data['assigned_agent']}' does not exist"
            )

    # Tracked fields — inme change ho to history mein likh do
    tracked_fields = ["status", "priority", "assigned_agent"]

    for field, value in update_data.items():
        old_value = getattr(ticket, field)
        if field in tracked_fields and old_value != value:
            history_service.log_change(db, ticket_id, field, old_value, value)
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return ticket