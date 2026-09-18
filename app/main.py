from fastapi import FastAPI

from app.database import Base, engine
from app.models import ticket, agent, comment
from app.routers import tickets, agents

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SupportDesk API")

app.include_router(tickets.router)
app.include_router(agents.router)
@app.get("/test")
def test_check():
    return {"status": "ok", "message": "SupportDesk is running"}