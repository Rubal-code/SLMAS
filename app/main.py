from fastapi import FastAPI
from dotenv import load_dotenv

from app.admin.approval import router as approval_router
from app.admin.feedback import router as feedback_router
from app.api.tasks import router as task_router
from app.db import init_db

load_dotenv()

app = FastAPI(title="SLMAS Agent", version="0.1.0")
app.include_router(task_router)
app.include_router(feedback_router)
app.include_router(approval_router)


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "SLMAS Agent - Phase 1 API ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
