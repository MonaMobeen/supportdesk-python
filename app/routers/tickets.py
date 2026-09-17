from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services import ticket_service

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