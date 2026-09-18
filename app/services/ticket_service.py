from sqlalchemy.orm import Session
from app.schemas.ticket import TicketUpdate
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate
from app.models.agent import Agent
from app.logger import logger
from app.config import OVERDUE_THRESHOLD_HOURS
from app.services import history_service
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import or_
from sqlalchemy import func as sql_func
import csv
import io

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
    logger.info(f"Ticket created: id={new_ticket.id}, title='{new_ticket.title}'")
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
                # NEW: Added warning log for invalid status transition
                logger.warning(
                    f"Invalid status transition attempted: "
                    f"{current_status} -> {new_status}"
                )
                raise ValueError(
                    f"Cannot change status from '{current_status}' to '{new_status}'"
                )

            if (
                new_status == "Closed"
                and not update_data.get("resolution_note")
                and not ticket.resolution_note
            ):
                # NEW: Added warning log when resolution note is missing
                logger.warning(
                    f"Attempted to close ticket {ticket_id} without a resolution note"
                )
                raise ValueError(
                    "Resolution note is required to close a ticket"
                )

            if (
                new_status in ["Resolved", "Closed"]
                and current_status not in ["Resolved", "Closed"]
            ):
                update_data["resolution_at"] = datetime.utcnow()

    if "assigned_agent" in update_data and update_data["assigned_agent"]:
        agent_exists = db.query(Agent).filter(
            Agent.name == update_data["assigned_agent"]
        ).first()

        if not agent_exists:
            # NEW: Added warning log when agent does not exist
            logger.warning(
                f"Attempted to assign ticket {ticket_id} to "
                f"non-existent agent '{update_data['assigned_agent']}'"
            )
            raise ValueError(
                f"Agent '{update_data['assigned_agent']}' does not exist"
            )

    tracked_fields = ["status", "priority", "assigned_agent"]

    for field, value in update_data.items():
        old_value = getattr(ticket, field)

        if field in tracked_fields and old_value != value:
            history_service.log_change(
                db, ticket_id, field, old_value, value
            )

        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)

    logger.info(
        f"Ticket updated: id={ticket_id}, fields={list(update_data.keys())}"
    )

    return ticket

REQUIRED_IMPORT_FIELDS = ["title", "description", "requester", "category"]
VALID_PRIORITIES = ["Low", "Medium", "High", "Critical"]


def import_tickets_from_csv(db: Session, file_contents: bytes):
    text = file_contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    successful = []
    failed = []

    for row_number, row in enumerate(reader, start=2):  # row 1 = header
        # Missing fields check karo
        missing = [f for f in REQUIRED_IMPORT_FIELDS if not row.get(f)]
        if missing:
            failed.append({
                "row": row_number,
                "reason": f"Missing required fields: {', '.join(missing)}"
            })
            continue

        priority = row.get("priority", "Medium").strip() or "Medium"
        if priority not in VALID_PRIORITIES:
            failed.append({
                "row": row_number,
                "reason": f"Invalid priority '{priority}'. Must be one of {VALID_PRIORITIES}"
            })
            continue

        try:
            new_ticket = Ticket(
                title=row["title"],
                description=row["description"],
                requester=row["requester"],
                category=row["category"],
                priority=priority,
            )
            db.add(new_ticket)
            db.commit()
            db.refresh(new_ticket)
            successful.append(new_ticket.id)
        except Exception as e:
            db.rollback()
            failed.append({"row": row_number, "reason": str(e)})

    return {
        "total_rows": len(successful) + len(failed),
        "successful_count": len(successful),
        "failed_count": len(failed),
        "successful_ticket_ids": successful,
        "failed_rows": failed,
    }


def export_tickets_to_csv(tickets):
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "id", "title", "description", "requester", "category",
        "priority", "status", "assigned_agent", "created_at", "updated_at"
    ])

    for t in tickets:
        writer.writerow([
            t.id, t.title, t.description, t.requester, t.category,
            t.priority, t.status, t.assigned_agent or "", t.created_at, t.updated_at
        ])

    output.seek(0)
    return output

def get_dashboard_summary(db: Session):
    total = db.query(Ticket).count()

    # Status ke hisaab se count
    status_counts = dict(
        db.query(Ticket.status, sql_func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )

    # Priority ke hisaab se count
    priority_counts = dict(
        db.query(Ticket.priority, sql_func.count(Ticket.id))
        .group_by(Ticket.priority)
        .all()
    )

    # Har agent ke paas kitne Open tickets hain
    open_by_agent = dict(
        db.query(Ticket.assigned_agent, sql_func.count(Ticket.id))
        .filter(Ticket.status.in_(["Open", "In Progress"]))
        .filter(Ticket.assigned_agent.isnot(None))
        .group_by(Ticket.assigned_agent)
        .all()
    )

    # Average resolution time (Resolved/Closed tickets ke liye)
    resolved_tickets = (
        db.query(Ticket)
        .filter(Ticket.status.in_(["Resolved", "Closed"]))
        .filter(Ticket.resolution_at.isnot(None))
        .all()
    )
    if resolved_tickets:
        total_seconds = sum(
            (t.resolution_at - t.created_at).total_seconds() for t in resolved_tickets
        )
        avg_hours = round((total_seconds / len(resolved_tickets)) / 3600, 2)
    else:
        avg_hours = None

    return {
        "total_tickets": total,
        "by_status": status_counts,
        "by_priority": priority_counts,
        "open_tickets_by_agent": open_by_agent,
        "average_resolution_time_hours": avg_hours,
    }


def get_overdue_tickets(db: Session):
    threshold_time = datetime.utcnow() - timedelta(hours=OVERDUE_THRESHOLD_HOURS)

    overdue = (
        db.query(Ticket)
        .filter(Ticket.status.in_(["Open", "In Progress"]))
        .filter(Ticket.created_at <= threshold_time)
        .all()
    )
    return overdue