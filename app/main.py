from fastapi import FastAPI

from app.database import Base, engine
from app.models import ticket
from app.routers import tickets

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SupportDesk API")

app.include_router(tickets.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "SupportDesk is running"}