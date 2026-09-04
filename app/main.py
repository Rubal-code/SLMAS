from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from app.admin.approval import router as approval_router
from app.admin.feedback import router as feedback_router
from app.api.tasks import router as task_router
from app.config import settings
from app.db import init_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.include_router(task_router)
app.include_router(feedback_router)
app.include_router(approval_router)


@app.get("/health")
async def health():
    return {"status": "ok", "environment": "production" if not settings.debug else "development"}


@app.get("/")
async def root():
    return {"message": "SLMAS Agent - Phase 8 production hardening started"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.debug)
