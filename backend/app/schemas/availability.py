"""Availability and Slot Pydantic schemas."""

from datetime import date, time
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AvailabilityBase(BaseModel):
    doctor_id: int
    appointment_date: date
    start_time: time
    end_time: time
    slot_duration_min: int = 30
    availability_status: str = "available"


class AvailabilityResponse(AvailabilityBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class SlotItem(BaseModel):
    slot_time: str  # Format: "HH:MM" e.g., "10:00"
    is_available: bool = True


class DaySlotsResponse(BaseModel):
    doctor_id: int
    doctor_name: str
    speciality: str
    appointment_date: str
    available_slots: List[str]
