"""Persistent Structured Conversation State for AI Voice Clinical Calls."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import json
import logging

logger = logging.getLogger(__name__)


class ConversationState(BaseModel):
    """
    Authoritative state tracked across multi-turn telephone / WebRTC calls.
    Prevents LLM amnesia, context loss, and hallucinated appointments.
    """
    session_id: str
    call_status: str = "active"  # connecting, active, ended, failed
    current_intent: Optional[str] = None  # CHECK_AVAILABILITY, BOOK_APPOINTMENT, CANCEL_APPOINTMENT, GENERAL_INQUIRY
    current_state: str = "LISTENING"
    workflow_status: str = "IDLE"  # IDLE, IN_PROGRESS, COMPLETED

    # Patient Identification
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    phone_confirmed: bool = False
    phone_readback_attempt: Optional[str] = None

    # Clinical Consultation Details
    requested_speciality: Optional[str] = None
    selected_doctor_id: Optional[int] = None
    selected_doctor_name: Optional[str] = None

    # Schedule Selection
    appointment_date: Optional[str] = None  # Normalized ISO 'YYYY-MM-DD'
    appointment_time: Optional[str] = None  # Normalized 'HH:MM' (24-hour)
    appointment_time_spoken: Optional[str] = None  # Spoken format (e.g. '10:00 AM')

    # Verified Backend Data
    available_doctors: List[Dict[str, Any]] = Field(default_factory=list)
    available_slots: List[str] = Field(default_factory=list)

    # Confirmation Flags & Outcomes
    booking_confirmation: bool = False
    cancellation_confirmation: bool = False
    booked_appointment_id: Optional[int] = None
    cancelled_appointment_id: Optional[int] = None

    # Contextual Memory & FSM Guards
    pending_action: Optional[str] = None  # e.g., 'AWAITING_DATE', 'AWAITING_TIME', 'AWAITING_PHONE_CONFIRMATION', 'AWAITING_BOOKING_CONFIRMATION'
    pending_question: Optional[str] = None  # Semantic pending question category
    last_question: Optional[str] = None  # Exact last prompt asked by the assistant
    last_tool_result: Optional[Dict[str, Any]] = None

    # Anti-Repetition & Deduplication Flags
    greeting_sent: bool = False
    turns_count: int = 0
    last_processed_utterance: Optional[str] = None
    last_processed_time: float = 0.0
    last_response_text: Optional[str] = None

    def update_intent(self, intent: str, new_state: Optional[str] = None):
        """Update active conversational intent without wiping existing details."""
        self.current_intent = intent
        if new_state:
            self.current_state = new_state

    def reset_for_new_booking(self):
        """Clear specific booking slot details while retaining patient phone/name."""
        self.appointment_date = None
        self.appointment_time = None
        self.appointment_time_spoken = None
        self.selected_doctor_id = None
        self.selected_doctor_name = None
        self.requested_speciality = None
        self.booking_confirmation = False
        self.booked_appointment_id = None
        self.available_slots = []
        self.pending_action = None
        self.pending_question = None
        self.current_intent = "BOOK_APPOINTMENT"
        self.current_state = "COLLECT_PREFERENCES"
        self.workflow_status = "IN_PROGRESS"

    def to_system_context(self) -> str:
        """
        Produce a concise, authoritative state summary injected into the LLM system prompt.
        The LLM must treat this as absolute truth.
        """
        lines = [
            "=== AUTHORITATIVE ACTIVE CONVERSATION STATE ===",
            f"- Current State: {self.current_state}",
            f"- Current Intent: {self.current_intent or 'Undetermined'}",
            f"- Patient Name: {self.patient_name or 'Not provided'}",
            f"- Patient Phone: {self.patient_phone or 'Not provided'} (Confirmed: {self.phone_confirmed})",
            f"- Requested Speciality: {self.requested_speciality or 'None selected'}",
            f"- Selected Doctor: {self.selected_doctor_name or 'None'} (ID: {self.selected_doctor_id or 'None'})",
            f"- Selected Appointment Date: {self.appointment_date or 'None selected'}",
            f"- Selected Appointment Time: {self.appointment_time_spoken or self.appointment_time or 'None selected'}",
            f"- Booking Confirmed: {self.booking_confirmation}",
            f"- Pending Action / Last Asked: {self.pending_action or 'None'}",
            f"- Greeting Already Sent: {self.greeting_sent}",
        ]
        if self.available_slots:
            lines.append(f"- Verified Available Slots for Selected Doctor: {', '.join(self.available_slots[:6])}")
        lines.append("CRITICAL: Never ask for information that is already provided and confirmed above!")
        lines.append("CRITICAL: If the user answers 'Yes', 'Tomorrow', '10 AM', or gives a name, resolve it using the Pending Action above.")
        lines.append("================================================")
        return "\n".join(lines)


class ConversationStateManager:
    """Session registry managing isolated, thread-safe ConversationState instances."""

    def __init__(self):
        self._states: Dict[str, ConversationState] = {}

    def get_or_create(self, session_id: str) -> ConversationState:
        """Retrieve existing state or initialize a clean one for the session."""
        if session_id not in self._states:
            self._states[session_id] = ConversationState(session_id=session_id)
            logger.info(f"Initialized new ConversationState for session {session_id}")
        return self._states[session_id]

    def get(self, session_id: str) -> Optional[ConversationState]:
        """Retrieve state if it exists."""
        return self._states.get(session_id)

    def remove(self, session_id: str):
        """Remove conversation state when call is terminated."""
        if session_id in self._states:
            del self._states[session_id]
            logger.info(f"Cleaned up ConversationState for session {session_id}")

    def list_active(self) -> List[ConversationState]:
        return list(self._states.values())


# Global singleton manager
conversation_state_manager = ConversationStateManager()
