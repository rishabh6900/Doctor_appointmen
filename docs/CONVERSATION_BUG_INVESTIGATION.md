# CarePoint AI Voice Agent — Conversation Bug Investigation & Action Plan

## 1. Executive Summary

This report documents the deep architectural and code-level investigation into the eight reported conversational issues in the **CarePoint Health Medical Clinic** AI voice receptionist.

The investigation confirmed that the core technical stack—**Pipecat 1.x, Google Gemini, ElevenLabs STT/TTS, Silero VAD, FastAPI, and SQLite WAL**—is properly installed and operational. However, critical logic disconnects exist between the frontend Web Speech / WebRTC event handling, the deterministic Finite State Machine (`FSMEngine`), the session state manager (`ConversationState`), and the date/time extraction routines. 

The most severe finding is that after a successful booking, the conversation state remained in `BOOKING_SUCCESS` without resetting pending slot parameters or offering a conversational exit/branch for subsequent turns (e.g., "thank you" or "book another"). Consequently, any follow-up utterance caused the FSM to re-evaluate the scheduling flow using the old confirmed slot, immediately triggering a duplicate booking confirmation. Furthermore, lack of utterance deduplication between Chromium interim silence-debounce timers and final STT events caused single spoken phrases to be submitted and answered twice.

All eight issues have been traced to exact source files, classes, and logic branches. A non-breaking, controlled implementation plan has been prepared.

---

## 2. Eight-Issue Investigation Table

| Issue | Root Cause | Exact File & Function / Class | Proposed Fix | Risk |
|---|---|---|---|---|
| **1. Duplicate AI Responses** | Web Speech API interim silence debounce (1200ms) dispatches `handleUserMessage(interim)`, and when `isFinal` arrives shortly after, it dispatches `handleUserMessage(finalTranscript)`. No utterance deduplication exists on frontend or backend. | `frontend/src/components/VoiceCallModal.tsx` (`initSpeechRecognition`, `handleUserMessage`); `backend/app/voice/interaction_service.py` (`interact`) | Add client-side utterance deduplication (`lastProcessedUtteranceRef` with 2.5s time window) and backend session-level turn idempotency cache (1.5s window). | Low. Genuine repeated phrases after 2.5s will still be processed normally. |
| **2. Previously Collected Date Is Asked Again** | In `_handle_scheduling_flow`, if date and time are supplied without a doctor, availability check auto-assigned `res["results"][0]` as the doctor. Later, when the caller specified the doctor, state was partially overwritten or re-evaluated because `AWAITING_DOCTOR` was not an explicit FSM state. | `backend/app/voice/fsm_engine.py` (`_extract_entities`, `_handle_scheduling_flow`) | Introduce explicit `AWAITING_DOCTOR_OR_SPECIALITY` state when date/time is provided without a doctor; preserve verified `appointment_date` and `appointment_time` across all subsequent doctor selections. | Low. Preserves slot details while allowing doctor disambiguation. |
| **3. Stale State After Successful Booking** | `_execute_final_booking` sets `current_state = "BOOKING_SUCCESS"` and clears `pending_action`, but leaves `appointment_date`, `appointment_time`, and `selected_doctor_id` populated. On the next turn (e.g. caller saying "Thank you"), the FSM fell through to `_handle_scheduling_flow`, which saw the old confirmed slot and re-prompted booking confirmation. | `backend/app/voice/fsm_engine.py` (`process_turn`, `_execute_final_booking`); `backend/app/voice/conversation_state.py` (`reset_for_new_booking`) | Add post-booking conversational states (`POST_BOOKING_IDLE`). When caller says "thank you", "bye", or "that's all", respond warmly without touching booking flow. When caller says "book another", call `state.reset_for_new_booking()`. | None. Completely resolves stale booking traps. |
| **4. Short Speech Misunderstood** | 1. Words representing numbers ("four PM", "ten AM") failed in `datetime_service.parse_time` because regex strictly expected `\d{1,2}` digits.<br>2. Short intent words ("new", "app", "book") were not mapped when answering initial prompts. | `backend/app/services/datetime_service.py` (`parse_time`); `backend/app/voice/fsm_engine.py` (`process_turn`, `_extract_entities`) | 1. Expand `parse_time` to parse word numerals ("one" through "twelve", "four pm").<br>2. Contextually resolve short utterances ("new", "app", "yes", "tomorrow") against `pending_action` and `last_question`. | Very Low. Enhances speech parser flexibility. |
| **5. Duplicate Transcript Events** | Race condition between `silenceTimerRef` and `recognition.onresult` `event.results[i].isFinal`. React generated random IDs (`Math.random()`) for transcript items instead of deterministic event IDs. | `frontend/src/components/VoiceCallModal.tsx` (`initSpeechRecognition`, `handleUserMessage`) | Introduce deterministic event tracking with unique sequential message IDs (`msg_${sessionId}_${turnCount}_${sender}`) and silence timer cancellation upon final transcript receipt. | None. Ensures single transcript rendering per utterance. |
| **6. Booking Confirmation Repeated** | Direct byproduct of Issue 3. Because state retained `patient_phone`, `phone_confirmed=True`, and slot details without an exit state, any subsequent conversational turn defaulted back to Step E (`_prompt_final_booking_confirmation`). | `backend/app/voice/fsm_engine.py` (`_handle_scheduling_flow`, lines 343-346) | Guard Step E with `if self.state.booking_confirmation: return _handle_post_booking_dialogue()`. Only transition to `CONFIRM_BOOKING` before initial execution. | None. Prevents re-confirmation of completed bookings. |
| **7. Unnecessary Patient Name Question** | While database schema and API contracts define `patient_name` as `nullable=True` (optional), ambiguous prompt wording or FSM fallbacks prompted the caller for a name even though the caller is uniquely identified by verbal phone number. | `backend/app/models/appointment.py`; `backend/app/voice/prompts.py`; `backend/app/voice/fsm_engine.py` | Explicitly enforce in system prompt and FSM that `patient_name` is strictly optional. Never prompt for patient name unless the caller volunteers it. Identification is 100% phone-based. | None. Matches exact client specifications. |
| **8. Repeated Appointment Questions** | Absence of a missing-field priority queue in `_handle_scheduling_flow`. The FSM checked fields out of order, re-prompting for date or specialty even when already present in `self.state`. | `backend/app/voice/fsm_engine.py` (`_handle_scheduling_flow`) | Implement strict missing-field ordering: (1) Specialty/Doctor -> (2) Date -> (3) Time -> (4) Phone -> (5) Confirmation. If a field is already confirmed in `self.state`, skip asking and retain the value. | Low. Eliminates redundant questions. |

---

## 3. Current Architecture

```
Caller Speech (Browser Mic)
       │
       ▼
WebRTC / Web Speech API (VoiceCallModal.tsx)
       │
       ▼ [POST /api/v1/voice/interact] (with session_id, message, history)
FastAPI Backend (backend/app/api/v1/endpoints/voice.py)
       │
       ▼
VoiceInteractionService (backend/app/voice/interaction_service.py)
       │
       ├──► Session & State Manager (ConversationStateManager / VoiceSessionManager)
       │
       ├──► Deterministic FSM Engine (FSMEngine - authoritative clinical logic & DB tools)
       │         │
       │         ├── check_doctor_availability (AvailabilityService)
       │         ├── book_appointment (AppointmentService)
       │         └── cancel_appointment (AppointmentService)
       │
       ├──► Google Gemini LLM (Natural spoken phrasing, 1-2 sentence constraint, no markdown)
       │
       ▼
FastAPI JSON Response (response_text, session_id, appointment_updated, current_state)
       │
       ▼
Browser UI (Transcript Rendering + Single Locked Speech Synthesis Audio / WebRTC remote audio)
```

---

## 4. Conversation State Analysis

- **Creation:** `ConversationStateManager.get_or_create(session_id)` initializes a fresh `ConversationState` instance when a new call begins.
- **Persistence:** State is maintained in-memory in the FastAPI application process for the duration of the call (`voice_session_manager` handles session lifecycle).
- **Updates:** `FSMEngine.process_turn()` mutates fields on `ConversationState` (`patient_phone`, `selected_doctor_name`, `appointment_date`, `appointment_time`, `pending_action`, `booking_confirmation`).
- **The Defect:** When a booking completes (`_execute_final_booking`), `booking_confirmation` is set to `True`, but `appointment_date` and `appointment_time` are not archived. Because `current_intent` remains `"BOOK_APPOINTMENT"`, any subsequent utterance triggers `_handle_scheduling_flow()`, causing the FSM to re-read the already-booked slot and repeat the confirmation prompt.
- **The Solution:** Add explicit workflow states: `COLLECT_PREFERENCES`, `PRESENT_SLOTS`, `CONFIRM_PHONE`, `CONFIRM_BOOKING`, `BOOKING_SUCCESS`, `POST_BOOKING_DIALOGUE`. Once `BOOKING_SUCCESS` is reached, subsequent non-booking phrases ("thank you", "goodbye") transition to `POST_BOOKING_DIALOGUE`, and requests for another booking call `reset_for_new_booking()`.

---

## 5. Duplicate Event Analysis

Two distinct duplicate mechanisms were discovered:
1. **Frontend Debounce Race Condition:**
   Chromium's `SpeechRecognition` fires intermediate `interim` results. If the user pauses for 1200ms, `silenceTimerRef` dispatches `handleUserMessage(interim)`. When `isFinal` arrives shortly after, it dispatches `handleUserMessage(finalTranscript)`.
2. **Backend Non-Idempotency:**
   The `/api/v1/voice/interact` endpoint processes every HTTP request without validating whether the exact same utterance was received less than 1.5 seconds ago on the same session.

**Resolution:**
- In `VoiceCallModal.tsx`:
  - Track `lastDispatchedTextRef` and `lastDispatchTimeRef`.
  - Cancel `silenceTimerRef` immediately upon receiving `finalTranscript` or new interim results.
  - Reject duplicate dispatch if text matches `lastDispatchedTextRef` within 2500ms.
- In `VoiceInteractionService`:
  - Cache `last_utterance`, `last_response`, and `last_timestamp` per session.
  - If a duplicate utterance is received within 1500ms, return the cached response without re-invoking the FSM or database tools.

---

## 6. Booking Lifecycle Analysis

### Existing Flawed Lifecycle:
```
COLLECT_DATE -> CHECK_AVAILABILITY -> AWAITING_TIME -> AWAITING_PHONE -> CONFIRM_PHONE -> CONFIRM_BOOKING -> EXECUTE_BOOKING -> BOOKING_SUCCESS
                                                                                                                      │
                                                     Caller says "Thank you" ◄────────────────────────────────────────┘
                                                              │
                                                              ▼
                                                     CONFIRM_BOOKING (Repeated Confirmation Bug!)
```

### Corrected Target Lifecycle:
```
COLLECT_SPECIALITY_OR_DOCTOR
       │
       ▼
COLLECT_DATE (Retain previously collected date/time if already provided)
       │
       ▼
CHECK_AVAILABILITY (Verified backend doctor schedules)
       │
       ▼
PRESENT_AVAILABLE_SLOTS (Offer top 3-4 slots)
       │
       ▼
COLLECT_PHONE (Identify caller; no mandatory name prompt)
       │
       ▼
CONFIRM_PHONE (Digit-by-digit readback verification)
       │
       ▼
FINAL_BOOKING_CONFIRMATION (Summarize doctor, date, time; require explicit yes)
       │
       ▼
EXECUTE_BOOKING (Atomic DB transaction with partial unique index)
       │
       ▼
BOOKING_COMPLETED (Reference # saved; pending actions cleared; workflow completed)
       │
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
Caller says "Thank you"        Caller says "Book another"        Caller asks clinic question
       │                                 │                                 │
       ▼                                 ▼                                 ▼
Warm closing response          Call reset_for_new_booking()      Answer general inquiry
(Do NOT repeat confirmation)   (Retain phone; reset slot)        (Keep booking intact)
```

---

## 7. Proposed Source Code Modifications

1. `backend/app/voice/conversation_state.py`:
   - Add `workflow_status: str = "IDLE"` (`IN_PROGRESS`, `COMPLETED`).
   - Add `pending_question: Optional[str] = None`.
   - Add `last_processed_utterance: Optional[str] = None` and `last_processed_time: float = 0.0`.
   - Update `reset_for_new_booking()` to transition state cleanly while preserving verified caller phone number.

2. `backend/app/voice/fsm_engine.py`:
   - Add post-booking intent handler: detect conversational closures ("thank you", "thanks", "bye", "have a good day") when `booking_confirmation` is `True`, responding with a gracious receptionist signoff.
   - Add "book another" / "new appointment" handler: trigger `reset_for_new_booking()` and transition to `COLLECT_PREFERENCES`.
   - Fix entity extraction & missing field hierarchy in `_handle_scheduling_flow`:
     - If date is supplied without doctor/specialty, ask: *"Which doctor or medical specialty would you prefer for [Date]?"*
     - If doctor is selected, preserve date and time without overwriting.
     - Never ask for patient name; remove name prompts from mandatory paths.
   - Support short speech recognition in `process_turn`: map "new", "app", "yes", "tomorrow", "four PM" directly against `pending_action`.

3. `backend/app/services/datetime_service.py`:
   - Enhance `parse_time` to recognize word-based hours ("one" to "twelve", "four PM", "ten AM", "two thirty").
   - Handle plain number answers when `pending_action == "AWAITING_TIME"` (e.g., user says "4" or "four" -> 16:00).

4. `backend/app/voice/interaction_service.py`:
   - Implement backend duplicate utterance deduplication cache (1.5-second idempotency window per session).
   - Enforce preservation of post-booking responses.

5. `frontend/src/components/VoiceCallModal.tsx`:
   - Fix `silenceTimerRef` cleanup and add `lastDispatchedTextRef` deduplication guard (2500ms window).
   - Assign deterministic unique IDs to transcript entries (`msg_${Date.now()}_${sender}`).

---

## 8. Test Plan

A comprehensive regression test suite will be added to `backend/tests/test_conversation_bug_fixes.py` verifying:
1. **Scenario 1 (New Appointment Intent):** "I want to book an appointment" -> asks for doctor or specialty.
2. **Scenario 2 (Short Response Intent):** Agent asks "Would you like to book an appointment or check availability?" -> Caller says "New" -> correctly transitions to booking.
3. **Scenario 3 (Date Retention):** Caller: "Tomorrow at 4 PM" -> Agent asks for doctor -> Caller: "Dr. Priya" -> State retains tomorrow at 16:00 with Dr. Priya.
4. **Scenario 4 (Phone Number Readback):** Caller provides phone number -> Agent reads back digits and asks for confirmation.
5. **Scenario 5 (Single Execution & Booking Reference):** Final confirmation -> executes `book_appointment` once, returns booking ID.
6. **Scenario 6 (Thank You After Booking):** Caller says "Thank you" after booking -> Agent responds politely without re-prompting confirmation.
7. **Scenario 7 (Book Another Appointment):** Caller says "I want to book another appointment" -> resets slot details, retains phone, begins new booking flow.
8. **Scenario 8 (Duplicate Transcript Deduplication):** Backend receives identical utterance within 1.5s -> returns cached response without duplicate execution.
9. **Scenario 9 (Genuine Repeated Speech):** Caller repeats same words after 3 seconds -> processes turn normally.
10. **Scenario 10 (Multi-Session Isolation):** Two separate session IDs maintain completely isolated states and appointment slots.
11. **Scenario 11 (Availability Query):** Caller asks for doctor availability -> calls `check_doctor_availability` and returns verified slots.
12. **Scenario 12 (Cancellation Confirmation Flow):** Caller requests cancellation -> verifies phone, disambiguates appointments, confirms before executing.

---

## 9. Risk Assessment

- **Risk of Breaking Existing 59 Tests:** Minimal. All existing API contracts (`/voice/interact`, `/voice/offer`, `/voice/sessions`) and function tool signatures (`check_doctor_availability`, `book_appointment`, `cancel_appointment`) remain strictly identical.
- **Risk of Dropping Legitimate Caller Input:** Mitigated by using a narrow deduplication window (1.5–2.5 seconds). Repetitions after 2.5 seconds are always treated as fresh input.
- **Risk of Database Locking:** SQLite WAL mode is preserved; all DB operations use existing scoped session patterns.

---

## 10. Execution Sequence

1. **Step 1:** Enhance `backend/app/services/datetime_service.py` (word-numeral time parsing).
2. **Step 2:** Update `backend/app/voice/conversation_state.py` (workflow states & deduplication fields).
3. **Step 3:** Refactor `backend/app/voice/fsm_engine.py` (post-booking handling, short speech resolution, missing-field ordering, no name prompting).
4. **Step 4:** Update `backend/app/voice/interaction_service.py` (turn deduplication cache).
5. **Step 5:** Update `frontend/src/components/VoiceCallModal.tsx` (frontend speech recognition debounce & deduplication).
6. **Step 6:** Create and execute `backend/tests/test_conversation_bug_fixes.py` (all 12 mandatory scenarios).
7. **Step 7:** Run the full test suite (`pytest backend/tests`) and verify 100% pass rate.
8. **Step 8:** Verify frontend compilation (`npm run build --prefix frontend`).
