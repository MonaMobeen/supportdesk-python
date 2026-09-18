from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.schemas.ticket import TicketCreate, TicketResponse, TicketUpdate
from app.database import SessionLocal
from app.services import ticket_service
from app.schemas.comment import CommentCreate, CommentResponse
from app.services import comment_service
from app.schemas.history import HistoryResponse
from app.services import history_service
from datetime import datetime
from typing import Optional
from datetime import datetime
router = APIRouter(prefix="/tickets", tags=["Tickets"])


# Har request ke liye database session dena aur khatam hone pe band karna
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=TicketResponse)
def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    return ticket_service.create_ticket(db, ticket)


@router.get("/")
def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    requester: Optional[str] = Query(None),
    assigned_agent: Optional[str] = Query(None),
    created_after: Optional[datetime] = Query(None),
    created_before: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    tickets, total = ticket_service.get_all_tickets(
        db,
        status=status,
        priority=priority,
        category=category,
        requester=requester,
        assigned_agent=assigned_agent,
        created_after=created_after,
        created_before=created_before,
        search=search,
        sort_by=sort_by,
        order=order,
        skip=skip,
        limit=limit,
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "results": [TicketResponse.model_validate(t) for t in tickets],
    }


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/{ticket_id}", response_model=TicketResponse)
def update_ticket(ticket_id: int, ticket: TicketUpdate, db: Session = Depends(get_db)):
    try:
        updated = ticket_service.update_ticket(db, ticket_id, ticket)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return updated

@router.post("/{ticket_id}/comments", response_model=CommentResponse)
def add_comment(ticket_id: int, comment: CommentCreate, db: Session = Depends(get_db)):
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return comment_service.create_comment(db, ticket_id, comment)


@router.get("/{ticket_id}/comments", response_model=List[CommentResponse])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return comment_service.get_comments_by_ticket(db, ticket_id)

@router.get("/{ticket_id}/history", response_model=List[HistoryResponse])
def get_ticket_history(ticket_id: int, db: Session = Depends(get_db)):
    ticket = ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return history_service.get_history_by_ticket(db, ticket_id)