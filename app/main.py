from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi import Request
from app.logger import logger
from app.database import Base, engine
from app.models import ticket, agent, comment, history, attachment
from app.routers import tickets, agents

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SupportDesk API")

app.include_router(tickets.router)
app.include_router(agents.router)
@app.get("/test")
def test_check():
    return {"status": "ok", "message": "SupportDesk is running"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )