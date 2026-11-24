"""Doctor repository for database operations."""

from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.doctor import Doctor


class DoctorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """Retrieve active or inactive doctor by ID."""
        return self.db.query(Doctor).filter(Doctor.id == doctor_id).first()

    def get_active_by_id(self, doctor_id: int) -> Optional[Doctor]:
        """Retrieve active doctor by ID."""
        return self.db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active.is_(True)).first()

    def list_doctors(
        self,
        speciality: Optional[str] = None,
        is_active: Optional[bool] = True,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Doctor], int]:
        """List doctors with filtering, search and pagination."""
        query = self.db.query(Doctor)

        if is_active is not None:
            query = query.filter(Doctor.is_active == is_active)

        if speciality:
            query = query.filter(func.lower(Doctor.speciality) == func.lower(speciality))

        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.filter(
                (func.lower(Doctor.name).like(search_term)) |
                (func.lower(Doctor.speciality).like(search_term))
            )

        total = query.count()
        doctors = query.order_by(Doctor.name).offset(skip).limit(limit).all()
        return doctors, total

    def get_specialities_with_counts(self) -> List[Tuple[str, int]]:
        """Retrieve distinct active specialties with doctor counts."""
        results = (
            self.db.query(Doctor.speciality, func.count(Doctor.id).label("doctor_count"))
            .filter(Doctor.is_active.is_(True))
            .group_by(Doctor.speciality)
            .order_by(Doctor.speciality)
            .all()
        )
        return results

    def create(self, doctor: Doctor) -> Doctor:
        """Create and persist a new doctor."""
        self.db.add(doctor)
        self.db.commit()
        self.db.refresh(doctor)
        return doctor
