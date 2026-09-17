from pydantic import BaseModel


class AgentCreate(BaseModel):
    name: str
    email: str


class AgentResponse(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True