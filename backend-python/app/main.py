"""FastAPI application entry point for LiftLog API v2."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.db.session import user_data_engine, rate_limit_engine
from app.api.routes import users, events, follow, inbox, shared, ai_workout, health
from app.api.websockets import ai_chat
from app.services.scheduler import get_scheduler

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Handles database initialization, background tasks, and cleanup.
    """
    # Startup: Create database tables
    async with user_data_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with rate_limit_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Start background scheduler
    scheduler = get_scheduler()
    scheduler.start()

    yield

    # Shutdown: Stop scheduler and close database connections
    scheduler.shutdown()
    await user_data_engine.dispose()
    await rate_limit_engine.dispose()


# Initialize FastAPI application
app = FastAPI(
    title="LiftLog API",
    version="2.0.0",
    description="Privacy-first fitness tracking backend with end-to-end encryption",
    lifespan=lifespan,
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(users.router, prefix="/v2")
app.include_router(events.router, prefix="/v2")
app.include_router(follow.router, prefix="/v2")
app.include_router(inbox.router, prefix="/v2")
app.include_router(shared.router, prefix="/v2")
app.include_router(ai_workout.router, prefix="/v2")
app.include_router(health.router)

# WebSocket endpoints
app.websocket("/ai-chat")(ai_chat.ai_chat_websocket)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "LiftLog API",
        "version": "2.0.0",
        "description": "Privacy-first fitness tracking backend",
    }
