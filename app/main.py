from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables from .env when present
load_dotenv()

app = FastAPI(title="SLMAS Agent (Phase 0)")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "SLMAS Agent - Phase 0 - Health OK"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
