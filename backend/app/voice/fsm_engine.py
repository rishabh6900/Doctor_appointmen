"""Finite State Machine (FSM) Conversational Dialogue Engine for Clinic Receptionist."""

import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.phone_utils import (
    clean_spoken_phone_input,
    normalize_spoken_phone_number,
    format_phone_digit_by_digit,
    generate_phone_confirmation_prompt,
    is_phone_correction,
)
from app.services.datetime_service import datetime_service
from app.services.availability_service import AvailabilityService
from app.repositories.doctor_repository import DoctorRepository
from app.voice.conversation_state import ConversationState
from app.voice.tools import (
    execute_check_doctor_availability,
    execute_book_appointment,
    execute_cancel_appointment,
)

logger = logging.getLogger(__name__)


class FSMEngine:
    """Deterministic, context-aware dialogue engine orchestrating state transitions."""

    def __init__(self, db: Session, state: ConversationState):
        self.db = db
        self.state = state
        self.doctor_repo = DoctorRepository(db)
        self.avail_service = AvailabilityService(db)

    def process_turn(self, user_text: str) -> Dict[str, Any]:
        """
        Process incoming patient turn against conversation state, execute verified tools,
        and generate a natural, professional clinical response.
        """
        self.state.turns_count += 1
        clean_text = user_text.strip()
        lower_text = clean_text.lower()
        tools_called: List[str] = []
        appointment_updated = False

        # 1. Emergency Safety Guard
        emergency_pattern = r"\b(chest pain|heart attack|stroke|difficulty breathing|unconscious|severe bleeding|emergency)\b"
        if re.search(emergency_pattern, lower_text):
            self.state.current_state = "EMERGENCY_DIVERT"
            return {
                "response_text": (
                    "If you are experiencing a medical emergency, please hang up immediately and dial your "
                    "local emergency services (112 or 911) or proceed immediately to the nearest hospital emergency room."
                ),
                "appointment_updated": False,
                "tools_called": [],
            }

        # 2. Greeting Handling (Strict One-Time Welcome)
        is_simple_greeting = bool(re.fullmatch(r"(?:hello|hi|hey|good morning|good afternoon|good evening)[.!]?", lower_text))
        if is_simple_greeting:
            if not self.state.greeting_sent:
                self.state.greeting_sent = True
                self.state.current_state = "LISTENING"
                return {
                    "response_text": (
                        f"Hello! Welcome to {settings.CLINIC_NAME}. I'm your AI appointment assistant. "
                        "Are you looking to check doctor availability, book an appointment, or cancel an existing one?"
                    ),
                    "appointment_updated": False,
                    "tools_called": [],
                }
            else:
                # Contextual greeting when caller says hello during active session
                if self.state.selected_doctor_name and self.state.appointment_date:
                    return {
                        "response_text": (
                            f"Hello! We were looking at Dr. {self.state.selected_doctor_name} for "
                            f"{self.state.appointment_date}. Would you like to select an appointment time?"
                        ),
                        "appointment_updated": False,
                        "tools_called": [],
                    }
                return {
                    "response_text": "Hello! How can I help you with your appointment today?",
                    "appointment_updated": False,
                    "tools_called": [],
                }

        # Ensure greeting is marked as sent for any substantive request
        self.state.greeting_sent = True

        # 3. Post-Booking Continuation / Closure (Prevents Replaying Confirmation)
        if self.state.booking_confirmation or self.state.current_state in ("BOOKING_SUCCESS", "POST_BOOKING_DIALOGUE"):
            # Acknowledge gratitude or closing remarks
            closure_pattern = r"\b(thank\s*you|thanks|okay\s*thanks|ok\s*thanks|bye|goodbye|that'?s\s*all|nothing\s*else|no\s*that'?s\s*it|that\s*will\s*be\s*all)\b"
            if re.search(closure_pattern, lower_text):
                self.state.current_state = "POST_BOOKING_DIALOGUE"
                self.state.workflow_status = "COMPLETED"
                return {
                    "response_text": "You're very welcome! If you need anything else, please don't hesitate to call. Have a wonderful day!",
                    "appointment_updated": False,
                    "tools_called": [],
                }

            # Start another booking cleanly without corrupting the completed one
            another_pattern = r"\b(another\s*appointment|book\s*another|new\s*appointment|another\s*booking|one\s*more|schedule\s*another)\b"
            if re.search(another_pattern, lower_text):
                self.state.reset_for_new_booking()
                return {
                    "response_text": "Certainly! I'd be glad to help book another appointment. Which doctor or medical speciality would you prefer?",
                    "appointment_updated": False,
                    "tools_called": [],
                }

        # 4. Short Intent Resolution
        short_book_words = ("new", "app", "appointment", "new appointment", "book", "schedule", "book appointment")
        if lower_text in short_book_words:
            if not self.state.selected_doctor_name and not self.state.appointment_date:
                self.state.current_intent = "BOOK_APPOINTMENT"
                self.state.workflow_status = "IN_PROGRESS"
                self.state.current_state = "COLLECT_PREFERENCES"
                self.state.pending_action = "AWAITING_DOCTOR_OR_SPECIALITY"
                return {
                    "response_text": "I'd be glad to help schedule an appointment. Which doctor or medical speciality are you interested in?",
                    "appointment_updated": False,
                    "tools_called": [],
                }

        # 5. Resolve Affirmation / Denial based on Pending Action
        is_affirmative = bool(re.search(r"\b(yes|yeah|yep|correct|that's right|confirm|sure|proceed|okay|ok|please do)\b", lower_text))
        is_negative = bool(re.search(r"\b(no|nope|not correct|wrong|cancel that|don't)\b", lower_text))

        # Check slot ordinal resolution if waiting for time (e.g. "first one", "earliest")
        if self.state.pending_action == "AWAITING_TIME" and self.state.available_slots:
            if re.search(r"\b(first|earliest|1st)\b", lower_text):
                slot = self.state.available_slots[0]
                self.state.appointment_time = slot
                self.state.appointment_time_spoken = datetime_service.format_time_for_speech(slot)
            elif re.search(r"\b(second|2nd)\b", lower_text) and len(self.state.available_slots) > 1:
                slot = self.state.available_slots[1]
                self.state.appointment_time = slot
                self.state.appointment_time_spoken = datetime_service.format_time_for_speech(slot)

        # Check phone confirmation resolution
        if self.state.pending_action == "AWAITING_PHONE_CONFIRMATION":
            # Check if user says: "Yes, but it's zero not O" or gives a correction
            if is_phone_correction(lower_text):
                # Update phone with zero
                if self.state.patient_phone:
                    self.state.patient_phone = re.sub(r"[oO]", "0", self.state.patient_phone)
                self.state.phone_confirmed = True
                self.state.pending_action = "AWAITING_BOOKING_CONFIRMATION"
                return self._prompt_final_booking_confirmation()

            if is_affirmative:
                self.state.phone_confirmed = True
                self.state.pending_action = "AWAITING_BOOKING_CONFIRMATION"
                return self._prompt_final_booking_confirmation()
            elif is_negative:
                self.state.patient_phone = None
                self.state.phone_confirmed = False
                self.state.pending_action = "AWAITING_PHONE"
                return {
                    "response_text": "Understood. Please state your 10-digit phone number clearly.",
                    "appointment_updated": False,
                    "tools_called": [],
                }

        # Check final booking execution resolution
        if self.state.pending_action == "AWAITING_BOOKING_CONFIRMATION":
            if is_affirmative:
                return self._execute_final_booking(tools_called)
            elif is_negative:
                self.state.pending_action = None
                return {
                    "response_text": "I have cancelled the booking process. Would you like to check another doctor or time slot?",
                    "appointment_updated": False,
                    "tools_called": [],
                }

        # Check cancellation confirmation resolution
        if self.state.pending_action == "AWAITING_CANCELLATION_CONFIRMATION":
            if is_affirmative:
                return self._execute_cancellation(tools_called)
            elif is_negative:
                self.state.pending_action = None
                return {
                    "response_text": "Understood, your appointment remains active and confirmed. Is there anything else I can assist you with?",
                    "appointment_updated": False,
                    "tools_called": [],
                }

        # 4. Extract Entities (Doctor, Speciality, Date, Time, Phone)
        self._extract_entities(clean_text)

        # 5. Route to Flow: Cancellation, Booking, or Availability
        if any(w in lower_text for w in ["cancel", "cancellation"]) or self.state.current_intent == "CANCEL_APPOINTMENT":
            return self._handle_cancellation_flow(clean_text, tools_called)

        # 6. Availability and Booking Flow
        return self._handle_scheduling_flow(clean_text, tools_called)

    def _extract_entities(self, text: str):
        """Extract doctors, specialties, dates, times, and phone numbers into state."""
        lower = text.lower()

        # Doctor match
        doctors, _ = self.doctor_repo.list_doctors(is_active=True, limit=100)
        for doc in doctors:
            # Check full name or first/last name
            parts = doc.name.lower().replace("dr.", "").strip().split()
            if doc.name.lower() in lower or any(len(p) > 3 and p in lower for p in parts):
                self.state.selected_doctor_id = doc.id
                self.state.selected_doctor_name = doc.name
                self.state.requested_speciality = doc.speciality
                break

        # Speciality match using synonyms and direct search
        spec_synonyms = {
            "cardiologist": "Cardiology",
            "cardiology": "Cardiology",
            "heart doctor": "Cardiology",
            "dermatologist": "Dermatology",
            "dermatology": "Dermatology",
            "skin doctor": "Dermatology",
            "pediatrician": "Pediatrics",
            "pediatrics": "Pediatrics",
            "child doctor": "Pediatrics",
            "neurologist": "Neurology",
            "neurology": "Neurology",
            "general physician": "General Medicine",
            "general medicine": "General Medicine",
        }
        for syn, spec_name in spec_synonyms.items():
            if syn in lower:
                self.state.requested_speciality = spec_name
                break

        # Check for unknown / unsupported medical specialties (e.g. psychologist, dentist, orthopedic)
        if not self.state.requested_speciality:
            unsupported_match = re.search(r"\b([a-z]+(?:ologist|iatrist|surgery|orthopedic|dentist|oncolog\w*|urolog\w*))\b", lower)
            if unsupported_match:
                self.state.requested_speciality = unsupported_match.group(1).title()

        # Date match using DateTimeService
        parsed_date, err = datetime_service.parse_relative_or_explicit_date(text)
        if parsed_date:
            self.state.appointment_date = parsed_date.isoformat()

        # Time match using DateTimeService
        parsed_time, _ = datetime_service.parse_time(text)
        if parsed_time:
            self.state.appointment_time = parsed_time
            self.state.appointment_time_spoken = datetime_service.format_time_for_speech(parsed_time)

        # Phone number match
        valid, e164, _ = normalize_spoken_phone_number(text)
        if valid and not self.state.phone_confirmed:
            self.state.patient_phone = e164
            self.state.phone_readback_attempt = e164

        # Patient name match (e.g. "my name is John Doe", "for Jane Smith")
        name_match = re.search(r"(?:my name is|for|patient name is)\s+([A-Za-z\s]{3,25})", text, re.IGNORECASE)
        if name_match:
            cand = name_match.group(1).strip()
            # Ignore command words
            if cand.lower() not in ("cardiology", "dermatology", "pediatrics", "tomorrow", "today", "an appointment"):
                self.state.patient_name = cand.title()

    def _handle_scheduling_flow(self, text: str, tools_called: List[str]) -> Dict[str, Any]:
        """Orchestrate availability checking, slot presentation, and booking transitions."""
        self.state.current_intent = "BOOK_APPOINTMENT"
        self.state.workflow_status = "IN_PROGRESS"

        # Guard: If booking is already confirmed, do not re-prompt confirmation
        if self.state.booking_confirmation:
            return {
                "response_text": (
                    f"Your appointment is already confirmed (Reference #{self.state.booked_appointment_id}). "
                    "If you would like to schedule another appointment, please let me know!"
                ),
                "appointment_updated": False,
                "tools_called": [],
            }

        # Speciality validation (eliminate non-existent specialties)
        if self.state.requested_speciality:
            distinct_specs = [s[0] for s in self.doctor_repo.get_specialities_with_counts()]
            valid_specs = [s.lower() for s in distinct_specs]
            if self.state.requested_speciality.lower() not in valid_specs:
                available_str = ", ".join(distinct_specs)
                return {
                    "response_text": (
                        f"I'm sorry, our clinic does not currently offer {self.state.requested_speciality}. "
                        f"Our available medical specialties are: {available_str}."
                    ),
                    "appointment_updated": False,
                    "tools_called": [],
                }

        target_date_obj = datetime_service.get_clinic_today()
        if self.state.appointment_date:
            try:
                target_date_obj = target_date_obj.fromisoformat(self.state.appointment_date)
            except Exception:
                pass
        date_spoken = datetime_service.format_date_for_speech(target_date_obj)

        # Step A: Missing Doctor AND Speciality (retain previously collected date/time)
        if not self.state.selected_doctor_name and not self.state.requested_speciality:
            self.state.current_state = "COLLECT_PREFERENCES"
            self.state.pending_action = "AWAITING_DOCTOR_OR_SPECIALITY"
            if self.state.appointment_date:
                time_part = f" at {self.state.appointment_time_spoken}" if self.state.appointment_time_spoken else ""
                prompt = f"Certainly! Which doctor or medical speciality would you prefer for {date_spoken}{time_part}?"
            else:
                prompt = "I'd be glad to help schedule an appointment. Which doctor or medical speciality are you interested in?"
            return {
                "response_text": prompt,
                "appointment_updated": False,
                "tools_called": [],
            }

        # Step B: Missing Date
        if not self.state.appointment_date:
            self.state.current_state = "COLLECT_PREFERENCES"
            self.state.pending_action = "AWAITING_DATE"
            if self.state.selected_doctor_name:
                prompt = f"Certainly! For what date would you like to schedule with Dr. {self.state.selected_doctor_name}? (For example: tomorrow, or a specific date)"
            elif self.state.requested_speciality:
                prompt = f"Certainly! What date would you prefer for your {self.state.requested_speciality} consultation?"
            else:
                prompt = "I'd be glad to help schedule an appointment. For what date would you like your appointment?"
            return {
                "response_text": prompt,
                "appointment_updated": False,
                "tools_called": [],
            }

        # Step C: Execute Availability Check if slots not yet fetched for this doctor & date
        if not self.state.available_slots or self.state.pending_action in ("AWAITING_DATE", "AWAITING_DOCTOR_OR_SPECIALITY"):
            tools_called.append("check_doctor_availability")
            res = execute_check_doctor_availability(
                db=self.db,
                doctor_name=self.state.selected_doctor_name,
                speciality=self.state.requested_speciality,
                appointment_date=self.state.appointment_date,
            )
            self.state.last_tool_result = res

            if res.get("status") == "success" and res.get("results"):
                first_match = res["results"][0]
                if not self.state.selected_doctor_id or not self.state.selected_doctor_name:
                    self.state.selected_doctor_id = first_match["doctor_id"]
                    self.state.selected_doctor_name = first_match["doctor_name"]
                    self.state.requested_speciality = first_match["speciality"]
                schedules = first_match.get("schedules", [])
                if schedules:
                    slots = schedules[0].get("time_slots") or schedules[0].get("available_slots") or []
                    self.state.available_slots = slots
                else:
                    self.state.available_slots = []
            else:
                self.state.available_slots = []

        doc_display_name = self.state.selected_doctor_name if (self.state.selected_doctor_name and self.state.selected_doctor_name.startswith("Dr.")) else f"Dr. {self.state.selected_doctor_name or 'our physicians'}"

        if not self.state.available_slots:
            return {
                "response_text": f"I checked our schedule, and {doc_display_name} has no open slots on {date_spoken}. Would you like to check the following day or another doctor?",
                "appointment_updated": False,
                "tools_called": tools_called,
            }

        # Step D: Present slots and collect preferred time
        if not self.state.appointment_time:
            self.state.current_state = "PRESENT_AVAILABLE_SLOTS"
            self.state.pending_action = "AWAITING_TIME"
            # Format top 4 slots
            formatted_slots = [datetime_service.format_time_for_speech(s) for s in self.state.available_slots[:4]]
            slots_str = ", ".join(formatted_slots)
            return {
                "response_text": (
                    f"{doc_display_name} has open consultation slots on {date_spoken} at: "
                    f"{slots_str}. Which time works best for you?"
                ),
                "appointment_updated": False,
                "tools_called": tools_called,
            }

        # Step E: Preferred time selected; collect and confirm phone (NO mandatory name question)
        if not self.state.patient_phone or not self.state.phone_confirmed:
            if not self.state.patient_phone:
                self.state.current_state = "COLLECT_DETAILS"
                self.state.pending_action = "AWAITING_PHONE"
                return {
                    "response_text": (
                        f"Great, I have noted {self.state.appointment_time_spoken} on {date_spoken}. "
                        "To reserve your appointment, what is your telephone number?"
                    ),
                    "appointment_updated": False,
                    "tools_called": tools_called,
                }
            else:
                # Phone was extracted; ask for readback confirmation
                self.state.current_state = "CONFIRM_PHONE"
                self.state.pending_action = "AWAITING_PHONE_CONFIRMATION"
                confirm_prompt = generate_phone_confirmation_prompt(self.state.patient_phone)
                return {
                    "response_text": confirm_prompt,
                    "appointment_updated": False,
                    "tools_called": tools_called,
                }

        # Step F: Phone confirmed; ask for final verbal booking confirmation
        self.state.current_state = "CONFIRM_BOOKING"
        self.state.pending_action = "AWAITING_BOOKING_CONFIRMATION"
        return self._prompt_final_booking_confirmation()

    def _prompt_final_booking_confirmation(self) -> Dict[str, Any]:
        """Generate dual-stage final booking verification prompt."""
        self.state.current_state = "CONFIRM_BOOKING"
        self.state.pending_action = "AWAITING_BOOKING_CONFIRMATION"
        
        target_date_obj = datetime_service.get_clinic_today()
        if self.state.appointment_date:
            try:
                target_date_obj = target_date_obj.fromisoformat(self.state.appointment_date)
            except Exception:
                pass
        date_spoken = datetime_service.format_date_for_speech(target_date_obj)
        doc_display = self.state.selected_doctor_name if (self.state.selected_doctor_name and self.state.selected_doctor_name.startswith("Dr.")) else f"Dr. {self.state.selected_doctor_name or 'our physician'}"

        patient_name_part = f" for {self.state.patient_name}" if self.state.patient_name else ""
        return {
            "response_text": (
                f"Thank you. To confirm, I am booking an appointment with {doc_display} "
                f"({self.state.requested_speciality}) on {date_spoken} at {self.state.appointment_time_spoken}{patient_name_part}. "
                "Shall I confirm this reservation?"
            ),
            "appointment_updated": False,
            "tools_called": [],
        }

    def _execute_final_booking(self, tools_called: List[str]) -> Dict[str, Any]:
        """Execute atomic database booking."""
        tools_called.append("book_appointment")
        res = execute_book_appointment(
            db=self.db,
            patient_phone_number=self.state.patient_phone or "",
            doctor_id=self.state.selected_doctor_id or 1,
            appointment_date=self.state.appointment_date or "",
            appointment_time=self.state.appointment_time or "",
            patient_name=self.state.patient_name,
            phone_readback_confirmed=True,
            action_confirmed=True,
        )

        if res.get("status") == "confirmed":
            self.state.current_state = "BOOKING_SUCCESS"
            self.state.workflow_status = "COMPLETED"
            self.state.booking_confirmation = True
            self.state.booked_appointment_id = res.get("booking_id")
            self.state.pending_action = None

            target_date_obj = datetime_service.get_clinic_today()
            if self.state.appointment_date:
                try:
                    target_date_obj = target_date_obj.fromisoformat(self.state.appointment_date)
                except Exception:
                    pass
            date_spoken = datetime_service.format_date_for_speech(target_date_obj)
            doc_display = self.state.selected_doctor_name if (self.state.selected_doctor_name and self.state.selected_doctor_name.startswith("Dr.")) else f"Dr. {self.state.selected_doctor_name or 'our physician'}"

            return {
                "response_text": (
                    f"Your appointment with {doc_display} on {date_spoken} at "
                    f"{self.state.appointment_time_spoken} has been officially confirmed! "
                    f"Your booking reference is #{res.get('booking_id')}. Is there anything else I can help you with today?"
                ),
                "appointment_updated": True,
                "tools_called": tools_called,
            }
        else:
            return {
                "response_text": f"I apologize, but we could not complete the reservation: {res.get('message', 'Slot conflict')}. Would you like to select another time?",
                "appointment_updated": False,
                "tools_called": tools_called,
            }

    def _handle_cancellation_flow(self, text: str, tools_called: List[str]) -> Dict[str, Any]:
        """Orchestrate cancellation disambiguation and execution."""
        self.state.current_intent = "CANCEL_APPOINTMENT"

        if not self.state.patient_phone:
            self.state.current_state = "COLLECT_PHONE"
            self.state.pending_action = "AWAITING_PHONE_FOR_CANCEL"
            return {
                "response_text": "I can certainly assist with cancelling an appointment. May I have your phone number to locate your booking?",
                "appointment_updated": False,
                "tools_called": tools_called,
            }

        # Search appointments for phone
        tools_called.append("cancel_appointment")
        res = execute_cancel_appointment(
            db=self.db,
            patient_phone_number=self.state.patient_phone,
            phone_readback_confirmed=True,
            action_confirmed=False,
        )

        if res.get("status") in ("none_found", "error"):
            return {
                "response_text": "I couldn't locate any active appointments under that telephone number. Please verify your phone number.",
                "appointment_updated": False,
                "tools_called": tools_called,
            }

        if res.get("status") in ("multiple_found", "disambiguation_required"):
            items = res.get("appointments", [])
            summary = ", ".join([f"Appointment #{a.get('appointment_id', a.get('id'))} on {a.get('date', a.get('appointment_date'))} at {a.get('time', a.get('appointment_time'))}" for a in items])
            self.state.pending_action = "AWAITING_APPOINTMENT_ID_SELECTION"
            return {
                "response_text": f"I found multiple appointments under your phone: {summary}. Which appointment ID would you like to cancel?",
                "appointment_updated": False,
                "tools_called": tools_called,
            }

        if res.get("status") in ("awaiting_confirmation", "action_confirmation_required"):
            self.state.current_state = "CONFIRM_CANCELLATION"
            self.state.pending_action = "AWAITING_CANCELLATION_CONFIRMATION"
            app_id = res.get("appointment_id")
            self.state.cancelled_appointment_id = app_id
            date_val = res.get("date") or res.get("appointment_date")
            time_val = res.get("time") or res.get("appointment_time")
            return {
                "response_text": f"I have located your appointment #{app_id} with Dr. {res.get('doctor_name')} on {date_val} at {time_val}. Are you sure you wish to cancel this appointment?",
                "appointment_updated": False,
                "tools_called": tools_called,
            }

        return {
            "response_text": "Could you please state the appointment details you wish to cancel?",
            "appointment_updated": False,
            "tools_called": tools_called,
        }

    def _execute_cancellation(self, tools_called: List[str]) -> Dict[str, Any]:
        """Execute atomic cancellation once confirmed."""
        tools_called.append("cancel_appointment")
        res = execute_cancel_appointment(
            db=self.db,
            patient_phone_number=self.state.patient_phone or "",
            appointment_id=self.state.cancelled_appointment_id,
            phone_readback_confirmed=True,
            action_confirmed=True,
        )

        if res.get("status") == "cancelled":
            self.state.current_state = "CANCELLATION_SUCCESS"
            self.state.workflow_status = "COMPLETED"
            self.state.cancellation_confirmation = True
            self.state.pending_action = None
            return {
                "response_text": f"Your appointment #{res.get('appointment_id')} has been successfully cancelled. The time slot has been returned to clinic availability. Is there anything else I can do for you?",
                "appointment_updated": True,
                "tools_called": tools_called,
            }
        else:
            return {
                "response_text": f"Could not cancel appointment: {res.get('message', 'Please check your appointment details.')}",
                "appointment_updated": False,
                "tools_called": tools_called,
            }
