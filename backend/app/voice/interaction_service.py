"""Conversational voice interaction service orchestrating FSM engine, Gemini LLM, and tools."""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from google import genai
from google.genai import types

from app.core.config import settings
from app.voice.prompts import get_system_prompt, format_dynamic_context
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
        import time
        session = voice_session_manager.get_or_create_session(session_id)
        state = conversation_state_manager.get_or_create(session.session_id)

        now = time.time()
        clean_msg = message.strip()

        # Idempotency Guard: Suppress identical utterance duplicates within 3.0s window
        if (
            state.last_processed_utterance
            and state.last_processed_utterance.lower() == clean_msg.lower()
            and (now - state.last_processed_time) < 3.0
            and state.last_response_text
        ):
            logger.info(f"[{session.session_id}] Duplicate utterance suppressed: '{clean_msg}'")
            return {
                "session_id": session.session_id,
                "response_text": state.last_response_text,
                "appointment_updated": False,
                "tools_called": [],
                "current_state": state.current_state,
            }

        # 1. Run deterministic FSM engine turn
        fsm = FSMEngine(db=self.db, state=state)
        fsm_result = fsm.process_turn(clean_msg)

        # 2. Synchronize session properties
        if state.patient_phone:
            session.patient_phone = state.patient_phone
        session.touch()

        # 3. Dynamic LLM conversational enhancement & natural spoken phrasing
        # The FSM provides authoritative clinical correctness; Gemini delivers natural human flow
        response_text = fsm_result["response_text"]

        # Only pass to Gemini if it's general conversational dialogue and not critical clinical confirmation states
        exact_states = ("EMERGENCY_DIVERT", "CONFIRM_PHONE", "CONFIRM_BOOKING", "CONFIRM_CANCELLATION", "BOOKING_SUCCESS", "CANCELLATION_SUCCESS")
        if self.client and state.current_state not in exact_states:
            try:
                system_prompt = get_system_prompt(self.clinic_today)
                dynamic_context = format_dynamic_context(state.model_dump(), history)
                
                prompt = (
                    f"{system_prompt}\n\n"
                    f"{dynamic_context}\n\n"
                    f"--- CURRENT TURN ---\n"
                    f"Caller Utterance: \"{clean_msg}\"\n"
                    f"Authoritative Clinical Facts & Response: \"{response_text}\"\n\n"
                    "INSTRUCTIONS FOR YOUR RESPONSE:\n"
                    "1. Answer what the caller asked directly in natural, spoken English (1-2 short sentences).\n"
                    "2. Ask at most ONE next necessary question. Do NOT ask for information already confirmed in the context.\n"
                    "3. If the caller made a correction, acknowledge it smoothly without restarting the conversation.\n"
                    "4. Strictly maintain continuity with the ongoing appointment flow.\n"
                    "5. NEVER use markdown formatting (no asterisks, no bullets, no symbols, no JSON). Spoken output only.\n"
                    "6. NEVER invent any doctors, dates, times, or slots not verified in the context above."
                )

                gemini_resp = self.client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=120,
                    ),
                )
                if gemini_resp and gemini_resp.text and len(gemini_resp.text.strip()) > 5:
                    refined = gemini_resp.text.strip()
                    # Strip any accidental markdown formatting
                    refined = refined.replace("*", "").replace("#", "").replace("- ", "").strip()
                    # Ensure phone numbers or critical appointment details are never dropped
                    if not (state.patient_phone and state.patient_phone not in refined and "heard" in response_text):
                        response_text = refined
            except Exception as exc:
                logger.debug(f"LLM refinement bypassed ({exc}); using authoritative FSM response.")

        # Cache response for duplicate suppression
        state.last_processed_utterance = clean_msg
        state.last_processed_time = time.time()
        state.last_response_text = response_text

        return {
            "session_id": session.session_id,
            "response_text": response_text,
            "appointment_updated": fsm_result.get("appointment_updated", False),
            "tools_called": fsm_result.get("tools_called", []),
            "current_state": state.current_state,
        }
