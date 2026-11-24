"""Export schemas."""

from app.schemas.common import HealthResponse, SpecialtyCountResponse, ErrorResponse
from app.schemas.doctor import DoctorBase, DoctorCreate, DoctorResponse, DoctorListResponse
from app.schemas.availability import AvailabilityBase, AvailabilityResponse, SlotItem, DaySlotsResponse
from app.schemas.appointment import (
    AppointmentBase,
    AppointmentCreate,
    AppointmentResponse,
    AppointmentDetailResponse,
    AppointmentListResponse,
)

__all__ = [
    "HealthResponse",
    "SpecialtyCountResponse",
    "ErrorResponse",
    "DoctorBase",
    "DoctorCreate",
    "DoctorResponse",
    "DoctorListResponse",
    "AvailabilityBase",
    "AvailabilityResponse",
    "SlotItem",
    "DaySlotsResponse",
    "AppointmentBase",
    "AppointmentCreate",
    "AppointmentResponse",
    "AppointmentDetailResponse",
    "AppointmentListResponse",
]
