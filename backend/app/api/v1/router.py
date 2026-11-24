"""API v1 Router aggregation."""

from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.doctors import router as doctors_router, speciality_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(doctors_router)
api_router.include_router(speciality_router)
