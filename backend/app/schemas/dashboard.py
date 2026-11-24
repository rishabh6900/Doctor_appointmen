"""Dashboard stats and metrics Pydantic schemas."""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.appointment import AppointmentResponse


class ActivityFeedItem(BaseModel):
    id: int
    patient_phone_masked: str
    patient_name: Optional[str]
    doctor_name: str
    speciality: str
    appointment_date: str
    appointment_time: str
    status: str
    created_at: datetime


class DashboardStatsResponse(BaseModel):
    total_doctors: int
    active_doctors: int
    total_appointments: int
    confirmed_appointments: int
    cancelled_appointments: int
    recent_activity: List[ActivityFeedItem]


class CancelAppointmentRequest(BaseModel):
    patient_phone_number: str
    phone_readback_confirmed: bool = True
    action_confirmed: bool = True


class CancelAppointmentResponse(BaseModel):
    status: str
    appointment_id: Optional[int] = None
    patient_phone_masked: str
    doctor_name: Optional[str] = None
    speciality: Optional[str] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    message: str
    appointments: Optional[List[dict]] = None
