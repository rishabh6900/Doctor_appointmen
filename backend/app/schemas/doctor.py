"""Doctor Pydantic schemas."""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class DoctorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120, description="Doctor full name")
    speciality: str = Field(..., min_length=2, max_length=80, description="Medical specialty")
    experience_years: int = Field(..., ge=0, le=70, description="Years of medical practice")
    description: Optional[str] = Field(None, description="Doctor biographical notes and expertise")
    is_active: bool = Field(True, description="Whether the doctor is currently active")


class DoctorCreate(DoctorBase):
    pass


class DoctorResponse(DoctorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class DoctorListResponse(BaseModel):
    total: int
    items: List[DoctorResponse]
