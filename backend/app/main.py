"""FastAPI Application Entrypoint."""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import Base, engine, SessionLocal
from app.database.seed import seed_database
from app.api.v1.router import api_router
from app.api.v1.endpoints.health import router as root_health_router
from app.api.v1.endpoints.voice import router as root_voice_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("appointment_system")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize database tables and seed data on startup."""
    # Only perform auto-init if not running under pytest
    if "pytest" not in sys.modules:
        logger.info("Initializing database schema...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_result = seed_database(db)
            logger.info(f"Seed verified on startup: {seed_result}")
        except Exception as exc:
            logger.warning(f"Seed initialization notice: {exc}")
        finally:
            db.close()

    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade AI Voice-Based Doctor Appointment Booking System Backend.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount root health check and API v1 router
app.include_router(root_health_router)  # Accessible at /health
app.include_router(root_voice_router)  # Accessible directly at /voice/*
app.include_router(api_router, prefix=settings.API_V1_PREFIX)  # Accessible at /api/v1/*
