import logging
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv

# Load .env BEFORE importing settings
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.admin.approval import router as approval_router
from app.admin.feedback import router as feedback_router
from app.api.tasks import router as task_router
from app.config import settings
from app.db import database_health, init_db


# --------------------------------------------------
# Logging
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger("slmas")


# --------------------------------------------------
# Application lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    if settings.secret_key == "change-me-in-production":
        logger.warning(
            "SECRET_KEY is still using the default development value. "
            "Update it for production deployments."
        )

    app.state.started_at = time.time()

    yield


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-ready self-learning AI agent backend",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Routers
# --------------------------------------------------

app.include_router(task_router)
app.include_router(feedback_router)
app.include_router(approval_router)


# --------------------------------------------------
# Request logging middleware
# --------------------------------------------------

@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    start = time.time()

    response = await call_next(request)

    process_time = round(
        (time.time() - start) * 1000,
        2,
    )

    logger.info(
        "HTTP %s %s completed in %sms with status %s",
        request.method,
        request.url.path,
        process_time,
        response.status_code,
    )

    return response


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.environment,
        "debug": settings.debug,
        "database": database_health(),
        "qdrant_url": settings.qdrant_url,
    }


# --------------------------------------------------
# Readiness endpoint
# --------------------------------------------------

@app.get("/ready")
async def readiness():
    db_status = database_health()

    status = (
        "ok"
        if db_status["status"] == "healthy"
        else "degraded"
    )

    return {
        "status": status,
        "database": db_status,
        "service": settings.app_name,
    }


# --------------------------------------------------
# Metrics endpoint
# --------------------------------------------------

@app.get("/metrics")
async def metrics():
    uptime = (
        time.time() - app.state.started_at
        if hasattr(app.state, "started_at")
        else 0
    )

    return {
        "service": settings.app_name,
        "status": "ok",
        "debug": settings.debug,
        "environment": settings.environment,
        "database": settings.database_url,
        "queue": settings.redis_url,
        "uptime_seconds": round(uptime, 2),
    }


# --------------------------------------------------
# Root endpoint
# --------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "SLMAS Agent is live",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# --------------------------------------------------
# Run directly
# --------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
    )