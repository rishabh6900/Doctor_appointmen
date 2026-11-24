"""Appointment Pydantic schemas."""

from datetime import date, time, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AppointmentBase(BaseModel):
    patient_phone_number: str = Field(..., description="Spoken patient phone number in E.164 format")
    patient_name: Optional[str] = Field(None, max_length=120, description="Patient name if collected")
    doctor_id: int = Field(..., description="Target doctor ID")
    appointment_date: date = Field(..., description="Appointment calendar date (YYYY-MM-DD)")
    appointment_time: time = Field(..., description="Appointment time slot (HH:MM:SS or HH:MM)")


class AppointmentCreate(AppointmentBase):
    phone_readback_confirmed: bool = Field(
        False,
        description="Server guard: True only if patient verbally confirmed readback of their phone number",
    )
    action_confirmed: bool = Field(
        False,
        description="Server guard: True only if patient explicitly gave final verbal confirmation to book",
    )


class AppointmentResponse(AppointmentBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppointmentDetailResponse(AppointmentResponse):
    doctor_name: str
    speciality: str


class AppointmentListResponse(BaseModel):
    total: int
    items: List[AppointmentResponse]
