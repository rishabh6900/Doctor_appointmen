"""Export voice tools and schemas."""

from app.voice.tools.availability_tool import (
    CHECK_AVAILABILITY_SCHEMA,
    execute_check_doctor_availability,
)
from app.voice.tools.booking_tool import (
    BOOK_APPOINTMENT_SCHEMA,
    execute_book_appointment,
)
from app.voice.tools.cancellation_tool import (
    CANCEL_APPOINTMENT_SCHEMA,
    execute_cancel_appointment,
)

VOICE_TOOLS = [
    CHECK_AVAILABILITY_SCHEMA,
    BOOK_APPOINTMENT_SCHEMA,
    CANCEL_APPOINTMENT_SCHEMA,
]

__all__ = [
    "VOICE_TOOLS",
    "CHECK_AVAILABILITY_SCHEMA",
    "BOOK_APPOINTMENT_SCHEMA",
    "CANCEL_APPOINTMENT_SCHEMA",
    "execute_check_doctor_availability",
    "execute_book_appointment",
    "execute_cancel_appointment",
]
