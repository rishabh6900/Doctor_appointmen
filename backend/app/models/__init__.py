"""Export all database models."""

from app.models.doctor import Doctor
from app.models.availability import Availability
from app.models.appointment import Appointment

__all__ = ["Doctor", "Availability", "Appointment"]
