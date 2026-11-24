# Gap Analysis: AI Voice-Based Doctor Appointment Booking System

**Analysis Date:** 24 November 2026  
**Auditor:** Principal Forward Deployed Engineer (FDE)

---

## 1. Requirements vs Actual Implementation Matrix

| Requirement / Component | Master Brief Specification | Current Repository Status | Gap Description | Priority | Recommended Action |
|---|---|---|---|---|---|
| **Phase 1 Architecture** | Complete research, system diagrams, DB schema, roadmap | **VERIFIED** | None. Fully documented in PDF & docs. | Complete | Approved baseline for subsequent phases. |
| **Backend Framework** | FastAPI with modular architecture (`api`, `core`, `services`, `models`) | **NOT STARTED** | Backend directory and FastAPI app do not exist. | **P0 (Immediate)** | Implement in Phase 2 using Python 3.12, FastAPI, and Pydantic v2. |
| **Database & ORM** | SQLite (WAL mode), SQLAlchemy 2.x, Alembic migrations | **NOT STARTED** | No models, migration environment, or SQLite file exist. | **P0 (Immediate)** | Create SQLAlchemy models and initial Alembic migration in Phase 2. |
| **Seed Data** | 8 doctors across 5+ specialties, 14-day availability slots | **NOT STARTED** | No seed script exists. | **P1** | Implement `seed.py` with realistic clinical schedules in Phase 2. |
| **Doctor & Availability APIs** | GET `/doctors`, `/specialities`, `/availability` | **NOT STARTED** | REST endpoints not implemented. | **P1** | Implement FastAPI routers in Phase 2. |
| **Appointment Business Logic** | Slot calculation, booking, cancellation, concurrency safety | **NOT STARTED** | Service layer not implemented. | **P0** | Implement in Phase 3 with atomic transactions. |
| **Concurrency & Double Booking** | Zero double bookings under simultaneous requests | **NOT STARTED** | Database partial index not yet created. | **P0** | Enforce `uq_active_slot` partial unique index in Phase 2/3. |
| **Phone Number Normalization** | Spoken digit parser & E.164 validator | **NOT STARTED** | No phone parsing utility exists. | **P1** | Implement utility using `phonenumbers` in Phase 3. |
| **Pipecat Voice Pipeline** | Pipecat 1.x pipeline: Transport -> STT -> VAD/Aggregator -> LLM -> TTS | **NOT STARTED** | Pipeline factory and session manager do not exist. | **P0** | Implement in Phase 4 using Pipecat 1.16+ API. |
| **ElevenLabs STT Integration** | Scribe v2 / Realtime WebSocket STT | **NOT STARTED** | Not implemented. | **P1** | Implement in Phase 4; conduct spike on latency & digit accuracy. |
| **Gemini LLM Integration** | Google Gemini Flash with function calling | **NOT STARTED** | Not implemented. | **P1** | Integrate `GoogleLLMService` in Phase 4. |
| **ElevenLabs TTS Integration** | Low-latency streaming TTS over WebSocket | **NOT STARTED** | Not implemented. | **P1** | Integrate `ElevenLabsTTSService` in Phase 4. |
| **Confirmation Guardrails** | Server-side verification of patient verbal consent | **NOT STARTED** | Guard logic not implemented. | **P0** | Implement multi-flag server checks in Phase 4 tool handlers. |
| **Frontend Dashboard** | React + TypeScript + Tailwind CSS dashboard | **NOT STARTED** | Frontend application not initialized. | **P1** | Bootstrap Vite + React + TS frontend in Phase 5. |
| **Phone Call UI** | Realistic phone modal with 6 states, audio waveform, transcript | **NOT STARTED** | Not implemented. | **P1** | Implement in Phase 5 using Web Audio API for true waveform. |
| **Real-Time Telemetry** | WebSocket `/ws/events` for transcript and appointments | **NOT STARTED** | Event hub and frontend hook not implemented. | **P1** | Implement in Phase 6. |
| **Test Suites** | Pytest unit, API, concurrency, voice tool tests | **NOT STARTED** | No tests currently exist. | **P1** | Build test suites incrementally across Phases 2, 3, 7. |
| **Docker & Deployment** | Dockerfile, docker-compose.yml, health checks | **NOT STARTED** | Container configurations do not exist. | **P2** | Implement in Phase 8. |
| **Final Comprehensive PDF** | 34-section exhaustive engineering guide | **PARTIAL** | Phase 1 PDF exists (23 pages). Final 34-section PDF pending. | **P2** | Compile complete guide upon Phase 8 completion. |

---

## 2. Identified Inconsistencies & Resolutions

1. **Phase 1 Status vs Code Generation:**
   - *Observation:* The master prompt instructs not to assume the repo is empty, but our inspection proves the repo contains Phase 1 documentation only.
   - *Resolution:* Respect the progress made in Phase 1 (do not re-do Phase 1 research) and proceed directly to Phase 2 (Backend Foundation).
2. **Pipecat API Version Discrepancy in Tutorials:**
   - *Observation:* Many online tutorials utilize Pipecat `0.0.x` signatures (`TransportParams(vad_analyzer=...)`, `model="gemini-..."`). Pipecat 1.x deprecates these in favor of `LLMUserAggregatorParams` and `Service.Settings`.
   - *Resolution:* As documented in the Phase 1 PDF, strictly adhere to the Pipecat 1.x architecture.
3. **Audio Transport Selection:**
   - *Observation:* The brief asks to evaluate WebRTC vs WebSockets.
   - *Resolution:* Adopt `SmallWebRTCTransport` for browser-to-Pipecat real-time audio and a dedicated WebSocket (`/ws/events`) for dashboard telemetry.
