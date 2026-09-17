from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.schemas.agent import AgentCreate


def create_agent(db: Session, agent_data: AgentCreate) -> Agent:
    new_agent = Agent(name=agent_data.name, email=agent_data.email)
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent


def get_all_agents(db: Session):
    return db.query(Agent).all()


def get_agent_by_name(db: Session, name: str):
    return db.query(Agent).filter(Agent.name == name).first()