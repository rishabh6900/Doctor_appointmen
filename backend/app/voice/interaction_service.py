"""Conversational voice interaction service orchestrating FSM engine, Gemini LLM, and tools."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from google import genai
from google.genai import types

from app.core.config import settings
from app.voice.prompts import get_system_prompt
from app.services.availability_service import AvailabilityService
from app.voice.session_manager import voice_session_manager
from app.voice.conversation_state import conversation_state_manager
from app.voice.fsm_engine import FSMEngine

logger = logging.getLogger(__name__)


class VoiceInteractionService:
    """Manages natural language dialogue reasoning, tool invocation, and state tracking."""

    def __init__(self, db: Session):
        self.db = db
        self.avail_service = AvailabilityService(db)
        self.clinic_today = self.avail_service.get_clinic_today()
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY) if settings.GOOGLE_API_KEY else None

    def interact(
        self,
        message: str,
        session_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process user spoken or typed query, invoke appropriate clinic tools,
        and generate a friendly, natural receptionist response.
        """
        session = voice_session_manager.get_or_create_session(session_id)
        state = conversation_state_manager.get_or_create(session.session_id)

        # 1. Run deterministic FSM engine turn
        fsm = FSMEngine(db=self.db, state=state)
        fsm_result = fsm.process_turn(message)

        # 2. Synchronize session properties
        if state.patient_phone:
            session.patient_phone = state.patient_phone
        session.touch()

        # 3. Optional LLM conversational enhancement (if online and not emergency)
        # If Gemini is available, we can refine the response while preserving all facts
        response_text = fsm_result["response_text"]

        # Only pass to Gemini if it's general conversational dialogue and not emergency
        if self.client and state.current_state not in ("EMERGENCY_DIVERT", "CONFIRM_PHONE", "CONFIRM_BOOKING"):
            try:
                system_context = state.to_system_context()
                prompt = (
                    f"{system_context}\n\n"
                    f"Verified Clinic Response to convey: \"{response_text}\"\n"
                    f"User said: \"{message}\"\n\n"
                    "Instructions: Rephrase the clinic response in a warm, polite, concise, professional tone (1-2 sentences). "
                    "Do NOT invent any new doctors, dates, times, or slots not mentioned above. Keep all specific dates, times, and numbers exactly as given."
                )

                gemini_resp = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=150,
                    ),
                )
                if gemini_resp and gemini_resp.text and len(gemini_resp.text.strip()) > 5:
                    refined = gemini_resp.text.strip()
                    # Ensure critical facts are preserved
                    if not (state.patient_phone and state.patient_phone not in refined and "heard" in response_text):
                        response_text = refined
            except Exception as exc:
                logger.debug(f"LLM refinement bypassed ({exc}); using authoritative FSM response.")

        return {
            "session_id": session.session_id,
            "response_text": response_text,
            "appointment_updated": fsm_result.get("appointment_updated", False),
            "tools_called": fsm_result.get("tools_called", []),
            "current_state": state.current_state,
        }
