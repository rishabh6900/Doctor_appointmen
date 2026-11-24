"""Common and shared Pydantic response models."""

from typing import Any, Optional, Dict
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    clinic_timezone: str
    clinic_name: str


class SpecialtyCountResponse(BaseModel):
    speciality: str
    doctor_count: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
