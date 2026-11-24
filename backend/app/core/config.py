"""Application configuration using Pydantic Settings."""

from typing import List, Any
import json
from pydantic import field_validator
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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("true", "1", "t", "yes", "y", "debug", "dev", "development"):
                return True
            if v_lower in ("false", "0", "f", "no", "n", "release", "prod", "production"):
                return False
        return bool(v)

    # Clinic Operations
    CLINIC_NAME: str = "CarePoint Health Medical Clinic"
    CLINIC_PHONE: str = "+1-800-555-0199"
    CLINIC_TIMEZONE: str = "Asia/Kolkata"
    DEFAULT_PHONE_REGION: str = "IN"
    CLINIC_OPEN_TIME: str = "09:00"
    CLINIC_CLOSE_TIME: str = "17:00"
    DEFAULT_SLOT_DURATION_MIN: int = 30

    @property
    def iana_timezone(self) -> str:
        """Translate Windows timezone names to standard IANA timezone strings."""
        tz_map = {
            "india standard time": "Asia/Kolkata",
            "ist": "Asia/Kolkata",
            "eastern standard time": "America/New_York",
            "est": "America/New_York",
            "central standard time": "America/Chicago",
            "cst": "America/Chicago",
            "pacific standard time": "America/Los_Angeles",
            "pst": "America/Los_Angeles",
            "greenwich standard time": "UTC",
            "gmt": "UTC",
        }
        cleaned = self.CLINIC_TIMEZONE.strip().lower()
        return tz_map.get(cleaned, self.CLINIC_TIMEZONE)

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
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"


settings = Settings()
