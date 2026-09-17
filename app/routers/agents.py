from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import SessionLocal
from app.schemas.agent import AgentCreate, AgentResponse
from app.services import agent_service

router = APIRouter(prefix="/agents", tags=["Agents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=AgentResponse)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    existing = agent_service.get_agent_by_name(db, agent.name)
    if existing:
        raise HTTPException(status_code=400, detail="Agent with this name already exists")
    return agent_service.create_agent(db, agent)


@router.get("/", response_model=List[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    return agent_service.get_all_agents(db)