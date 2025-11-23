"""FastAPI application entry point for LiftLog API v2."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from app.core.config import settings
from app.db.session import user_data_engine, rate_limit_engine
from app.api.routes import users, events, follow, inbox, shared, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    Handles database initialization and cleanup.
    """
    # Startup: Create database tables
    async with user_data_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with rate_limit_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield

    # Shutdown: Close database connections
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
app.include_router(health.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "LiftLog API",
        "version": "2.0.0",
        "description": "Privacy-first fitness tracking backend",
    }
