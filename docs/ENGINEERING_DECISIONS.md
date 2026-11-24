# Engineering Decisions & Client Alignment

**Document Date:** 24 November 2026  
**Auditor:** Principal Forward Deployed Engineer (FDE)  
**Status:** Architectural Baseline Established | Client Decisions Cataloged

---

## 1. Key Architectural Decisions Established in Phase 1

### ADR-01: Pipecat 1.x Pipeline Architecture
- **Context:** Pipecat underwent a major architectural transition between `0.0.x` and `1.x`. Older tutorials configure VAD on the transport and use deprecated parameter bags.
- **Decision:** Build strictly on the Pipecat 1.x line (`pipecat-ai>=1.16.0`).
- **Rationale:** 1.x separates frame transport from conversational turn detection. VAD is configured via `LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer(...))` and turn stopping uses `TurnAnalyzerUserTurnStopStrategy` (Smart Turn v3).

### ADR-02: Dual-Channel Real-Time Communication
- **Context:** The application requires low-latency bidirectional voice for the call interface and structured event streaming for the dashboard.
- **Decision:** Decouple audio streaming from application events:
  1. **Audio Path:** Peer-to-peer WebRTC via Pipecat's `SmallWebRTCTransport`.
  2. **Telemetry Path:** Dedicated FastAPI WebSocket endpoint (`/ws/events`) for transcript streaming, call state updates, and appointment mutation notifications.
- **Rationale:** Audio demands UDP-based jitter handling without TCP head-of-line blocking, while dashboard events demand ordered, reliable JSON delivery with automatic reconnect and REST synchronization.

### ADR-03: Concurrency Control via Database Partial Unique Index
- **Context:** In a medical booking system, two concurrent callers or web users attempting to book the same doctor slot must never produce a double booking. Application-level locks (e.g. in-memory mutexes) fail across multi-process workers.
- **Decision:** Enforce slot uniqueness at the database level using a partial unique index:
  ```sql
  CREATE UNIQUE INDEX uq_active_slot
  ON appointments (doctor_id, appointment_date, appointment_time)
  WHERE status = 'confirmed';
  ```
- **Rationale:** This index is supported identically in SQLite and PostgreSQL. It allows cancelled appointments to be preserved for historical audit while guaranteeing zero duplicate confirmed bookings under any level of concurrency.

### ADR-04: Server-Side Confirmation Guardrails
- **Context:** LLMs can hallucinate patient intent or execute tool calls prematurely. The brief strictly forbids booking or cancelling without explicit patient confirmation.
- **Decision:** Implement multi-stage server-side guard logic in tool handlers:
  1. The LLM must pass explicit boolean flags (`phone_readback_confirmed=True`, `action_confirmed=True`).
  2. The tool handler validates that the telephone number submitted matches the number confirmed during the session readback.
  3. A new final user utterance must have arrived between the readback prompt and the mutation call.
  4. Cancellations follow a two-stage pattern: Stage 1 returns matching appointments for verbal disambiguation; Stage 2 executes the cancellation upon confirmation.

### ADR-05: Inherent Limitations of Spoken-Phone Authentication
- **Context:** The brief specifies that patients are identified solely by spoken phone numbers without passwords, OTPs, or caller ID.
- **Decision:** Document clearly that spoken phone numbers do not provide secure authentication. Anyone with knowledge of a patient's phone number could theoretically query or cancel appointments.
- **Mitigation:** Rate-limit voice sessions, mask phone numbers in logs and frontend displays (`+1 (***) ***-1234`), use soft cancellations (retaining records in the database), and minimize disclosure of clinical data.

---

## 2. Client Decisions & Open Questions

The Phase 1 blueprint identified 14 decisions (D1–D14). The following decisions are marked **BLOCKING** before Phase 2 begins, along with our recommended engineering defaults:

| # | Question | Recommended Engineering Default | Client Impact / Status |
|---|---|---|---|
| **D1** | **Clinic Timezone & Operating Hours** | `America/New_York` (or local client timezone), working hours `09:00 - 17:00`, Monday through Saturday. | **BLOCKING:** Governs relative date resolution ("tomorrow", "next Monday") and slot generation. |
| **D2** | **Default Phone Number Region** | United States (`US`, `+1`) formatted as E.164. | **BLOCKING:** Required by `phonenumbers` parser to correctly interpret spoken 10-digit numbers. |
| **D3** | **Agent Language** | English (`en-US`). | **BLOCKING:** Sets STT/TTS models and system prompt language. |
| **D5** | **Deployment Target for Initial Testing** | `localhost` using `SmallWebRTCTransport`. | **BLOCKING:** If testing on public IP/domain, STUN/TURN ICE configurations are required. |

### Non-Blocking Engineering Recommendations (Proceeding with Defaults Unless Directed Otherwise)
- **D4 (Frontend Framework):** Vite + React + TypeScript (Fast, lightweight, optimal for single-page WebRTC dashboard).
- **D6 (Patient Name):** Collect patient name during booking as optional/nullable; phone number remains primary key.
- **D7 (AI Model Selection):** `gemini-2.5-flash` or `gemini-1.5-flash` with low-latency thinking; ElevenLabs Turbo v2.5 / Flash model.
- **D8 (ElevenLabs STT):** `ElevenLabsRealtimeSTTService` via WebSocket; fall back to segmented HTTP if needed.
- **D9 (Dashboard Access):** Demo mode without login; phone numbers masked on UI; write endpoints protected.
- **D10 (Cancellation Cutoff):** Any future confirmed appointment can be cancelled; past appointments cannot.
- **D11 (Transcript Persistence):** In-memory per live session for privacy; not persisted to DB unless requested.
- **D12 (API Keys):** Mock test adapters used for unit tests; live keys provided via `.env` for Phase 4 voice spike.
- **D13 (Safety Scope):** Refuse medical advice/diagnosis with a standard clinic disclaimer; advise calling 911/emergency services for emergencies.
- **D14 (Slot Duration):** Standard 30-minute consultation slots.
