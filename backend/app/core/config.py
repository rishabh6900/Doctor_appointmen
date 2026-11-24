"""Application configuration using Pydantic Settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Settings
    PROJECT_NAME: str = "AI Voice Doctor Appointment Booking"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Clinic Operations
    CLINIC_NAME: str = "CarePoint Health Medical Clinic"
    CLINIC_PHONE: str = "+1-800-555-0199"
    CLINIC_TIMEZONE: str = "America/New_York"
    DEFAULT_PHONE_REGION: str = "US"
    CLINIC_OPEN_TIME: str = "09:00"
    CLINIC_CLOSE_TIME: str = "17:00"
    DEFAULT_SLOT_DURATION_MIN: int = 30

    # Database
    DATABASE_URL: str = "sqlite:///./appointments.db"

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    REST_API_KEY: str = ""

    # AI Providers (used in Phase 4)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_MODEL_ID: str = "eleven_turbo_v2_5"
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"


settings = Settings()
