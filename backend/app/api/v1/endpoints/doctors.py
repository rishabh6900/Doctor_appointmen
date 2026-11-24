"""Doctor and Speciality REST endpoints."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor import DoctorResponse, DoctorListResponse
from app.schemas.common import SpecialtyCountResponse

router = APIRouter(prefix="/doctors", tags=["Doctors"])
speciality_router = APIRouter(prefix="/specialities", tags=["Specialities"])


@router.get(
    "",
    response_model=DoctorListResponse,
    status_code=status.HTTP_200_OK,
    summary="List doctors with filtering and search",
)
def list_doctors(
    speciality: Optional[str] = Query(None, description="Filter by medical speciality (e.g. Cardiology)"),
    search: Optional[str] = Query(None, description="Search across doctor name or speciality"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(50, ge=1, le=100, description="Pagination limit"),
    db: Session = Depends(get_db),
):
    """Retrieve a list of clinical doctors matching query criteria."""
    repo = DoctorRepository(db)
    doctors, total = repo.list_doctors(
        speciality=speciality,
        is_active=is_active,
        search=search,
        skip=skip,
        limit=limit,
    )
    return DoctorListResponse(total=total, items=doctors)


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get doctor details by ID",
)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve specific doctor details by their numeric ID."""
    repo = DoctorRepository(db)
    doctor = repo.get_active_by_id(doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {doctor_id} not found or inactive.",
        )
    return doctor


@speciality_router.get(
    "",
    response_model=List[SpecialtyCountResponse],
    status_code=status.HTTP_200_OK,
    summary="List distinct medical specialities with doctor counts",
)
def list_specialities(db: Session = Depends(get_db)):
    """Retrieve distinct specialties and number of available active doctors."""
    repo = DoctorRepository(db)
    rows = repo.get_specialities_with_counts()
    return [
        SpecialtyCountResponse(speciality=r[0], doctor_count=r[1])
        for r in rows
    ]
