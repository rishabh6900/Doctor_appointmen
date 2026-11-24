"""Health check endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.database.session import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application liveness and readiness probe",
)
def health_check(db: Session = Depends(get_db)):
    """Liveness probe verifying database connectivity and configuration."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=settings.VERSION,
        database=db_status,
        clinic_timezone=settings.CLINIC_TIMEZONE,
        clinic_name=settings.CLINIC_NAME,
    )
