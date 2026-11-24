"""Dashboard stats REST endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.phone_utils import mask_phone_number
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.dashboard import DashboardStatsResponse, ActivityFeedItem

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get clinical dashboard statistics and activity feed",
)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Retrieve operational totals and recent appointment activity for the dashboard."""
    repo = AppointmentRepository(db)
    raw = repo.get_dashboard_metrics()

    feed_items = [
        ActivityFeedItem(
            id=app.id,
            patient_phone_masked=mask_phone_number(app.patient_phone_number),
            patient_name=app.patient_name,
            doctor_name=app.doctor.name,
            speciality=app.doctor.speciality,
            appointment_date=app.appointment_date.isoformat(),
            appointment_time=app.appointment_time.strftime("%H:%M"),
            status=app.status,
            created_at=app.created_at,
        )
        for app in raw["recent_activity"]
    ]

    return DashboardStatsResponse(
        total_doctors=raw["total_doctors"],
        active_doctors=raw["active_doctors"],
        total_appointments=raw["total_appointments"],
        confirmed_appointments=raw["confirmed_appointments"],
        cancelled_appointments=raw["cancelled_appointments"],
        recent_activity=feed_items,
    )
