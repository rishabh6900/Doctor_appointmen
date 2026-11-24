# Repository Audit: AI-Powered Voice-Based Doctor Appointment Booking System

**Audit Date:** 24 November 2026  
**Auditor:** Principal Forward Deployed Engineer (FDE) & Senior Software Architect  
**Repository Path:** `d:\project_2023_2027\voice-based doctor appointmen`  
**Current Development Phase:** Phase 1 Complete (Design & Architecture Documented) — Ready for Phase 2 (Backend Foundation)

---

## 1. Executive Summary

A comprehensive repository inspection was conducted across the workspace. The repository represents an early-stage, enterprise-grade AI healthcare voice assistant project titled **"AI-Powered Voice-Based Doctor Appointment Booking System"**.

Prior to this audit, the repository contained two critical documents:
1. `readme.md` (29.8 KB): The foundational project master prompt detailing product vision, full technology requirements, 8 to 11 lifecycle phases, API specifications, voice pipeline criteria, acceptance tests, and FDE operational guidelines.
2. `Voice_Appointment_System_Phase1_Research_and_Architecture.pdf` (92.8 KB, 23 pages): The formal Phase 1 deliverable ("Requirement Analysis, Technical Research, Architecture and Implementation Roadmap"), authored on 24 November 2026.

**Key Audit Conclusion:**  
No application source code (backend, frontend, database models, voice pipeline, or Docker assets) has been created yet. The project has strictly completed **Phase 1 (Research and Architecture)** and is currently at the gate of **Phase 2 (Backend Foundation and Database)**, pending client sign-off on key design decisions (D1, D2, D3, D5).

---

## 2. Repository Structure

```
d:\project_2023_2027\voice-based doctor appointmen\
│
├── readme.md                                                      # Master Project Specification & Requirements
├── Voice_Appointment_System_Phase1_Research_and_Architecture.pdf  # Phase 1 Architecture Blueprint (23 pages)
│
└── docs/                                                          # Audit & Engineering Governance (Generated)
    ├── REPOSITORY_AUDIT.md                                        # This comprehensive repository audit report
    ├── IMPLEMENTATION_STATUS.md                                   # Real-time phase tracking & readiness status
    ├── GAP_ANALYSIS.md                                            # Requirement vs implementation gap matrix
    └── ENGINEERING_DECISIONS.md                                   # Architectural decisions & open client questions
```

### Git & Version Control Status
- **Git Repository:** Not currently initialized (`.git` directory not present).
- **Recommendation:** Initialize Git repository and commit initial Phase 1 artifacts before beginning Phase 2 code implementation.

---

## 3. Documentation Analysis

### 3.1 `readme.md` Analysis
- **Role Defined:** Principal FDE, Senior AI Voice Systems Engineer, Full-Stack Lead.
- **Product Scope:** Web-based virtual medical receptionist allowing patients to check doctor availability, book appointments, and cancel appointments using conversational voice in real time.
- **Core Technology Mandate:**
  - **Voice Pipeline:** Pipecat 1.x
  - **STT:** ElevenLabs Speech-to-Text (Scribe v2 / Realtime)
  - **TTS:** ElevenLabs Text-to-Speech (WebSocket streaming)
  - **LLM:** Google Gemini with low-latency thinking configuration
  - **VAD:** Silero VAD (16kHz / 8kHz)
  - **Backend:** FastAPI, Python 3.12, SQLAlchemy 2.x, Pydantic v2
  - **Database:** SQLite with WAL mode (PostgreSQL-ready schema)
  - **Frontend:** React / Vite or Next.js with TypeScript, Tailwind CSS, shadcn/ui
  - **Real-Time Layer:** WebRTC for bidirectional audio + WebSocket (`/ws/events`) for dashboard telemetry
  - **Deployment:** Docker & Docker Compose
- **Strict Constraints:**
  - Spoken phone number is the sole patient identifier (strictly no passwords, OTPs, or caller-ID).
  - Explicit confirmation guardrails for both booking and cancellation.
  - Strict administrative boundary: no medical diagnosis or triage advice.

### 3.2 `Voice_Appointment_System_Phase1_Research_and_Architecture.pdf` Analysis
The 23-page PDF is a high-quality engineering architecture report:
- **Pages 1–3:** Title, metadata, and exhaustive Table of Contents.
- **Page 4:** Executive Summary noting that Phase 1 (Research & Architecture) is documented, no application code has been written, and Pipecat 1.x patterns are selected.
- **Pages 5–6:** Condensed functional/non-functional requirements and 10 identified gaps/tensions (G1–G10).
- **Pages 7–8:** Technical research verified against official Pipecat 1.x documentation (`LLMUserAggregatorParams`, `SileroVADAnalyzer`, `ElevenLabsRealtimeSTTService`, `GoogleLLMService`, `SmallWebRTCTransport`).
- **Pages 9–12:** Layered architecture and pipeline dataflow diagrams; audio transport comparison table (SmallWebRTC vs plain WebSocket vs Daily).
- **Pages 13–14:** Database schema design with ER diagrams and crucial partial unique index:
  ```sql
  CREATE UNIQUE INDEX uq_active_slot
  ON appointments (doctor_id, appointment_date, appointment_time)
  WHERE status = 'confirmed';
  ```
- **Pages 15–16:** Multi-stage conversational state machine, server-side confirmation guardrails, digit normalization, and safety rules.
- **Page 17:** Complete REST API specification (`/api/v1/doctors`, `/availability`, `/appointments`, `/dashboard/stats`, `/voice/offer`, `/ws/events`, `/health`).
- **Page 18:** Security and privacy assessment detailing the unavoidable risks of spoken-phone-number authentication.
- **Page 19:** Testing matrix mapping the 8 acceptance tests to unit, integration, and voice harness layers.
- **Pages 20–21:** 8-phase implementation roadmap and risk register with implementation tracker (all phases 2–8 marked "Not started").
- **Pages 22–23:** 14 client decisions/open questions (D1–D14, with D1, D2, D3, D5 identified as blocking) and clickable documentation references.

---

## 4. Source Code & Component Audit

| Component | Status | Findings |
|---|---|---|
| **Backend (`/backend`)** | **NOT STARTED** | No FastAPI app, routers, models, services, or Alembic migrations exist. |
| **Database (`/database` / SQLite)** | **NOT STARTED** | No database file (`appointments.db`), models, or seed script exist. |
| **Voice Pipeline (`/backend/app/voice`)** | **NOT STARTED** | No Pipecat pipeline, tool handlers, or WebRTC signaling offer endpoints exist. |
| **Frontend (`/frontend`)** | **NOT STARTED** | No React/Vite/Next.js package, UI components, waveform canvas, or audio hooks exist. |
| **Tests (`/tests` / `/backend/tests`)** | **NOT STARTED** | No test suites, pytest configurations, or mock fixtures exist. |
| **DevOps / Docker** | **NOT STARTED** | No Dockerfile, docker-compose.yml, or .env files exist. |

---

## 5. Technology Stack & Host Environment Verification

We performed system checks on the host environment:
- **Operating System:** Windows 11 / Server (x64)
- **Python Version:** `Python 3.12.2` (Verified; matches Pipecat 1.16 recommended Python 3.12 runtime)
- **Node.js Version:** `v24.19.0` (Verified; modern LTS-capable runtime)
- **npm Version:** `11.17.0` (Verified)
- **Docker Version:** `Docker 29.8.0` (Verified; available for containerization)
- **Git Version:** `git 2.46.0.windows.1` (Verified; available for version control)

All host tooling is compatible with the project requirements.

---

## 6. Technical Risks & Mitigations

1. **Pipecat 1.x API Evolution:**
   - *Risk:* 1.x uses `LLMContextAggregatorPair` and `Service.Settings` instead of deprecated `0.0.x` parameters.
   - *Mitigation:* Pin exact versions (`pipecat-ai>=1.16.0`) and conduct a focused spike in Phase 4.
2. **Double Booking Under High Concurrency:**
   - *Risk:* Race conditions during simultaneous voice calls for the same doctor slot.
   - *Mitigation:* Enforced at the database engine level via SQLite/PostgreSQL partial unique index `uq_active_slot` within an atomic write transaction.
3. **LLM Hallucinating Confirmation:**
   - *Risk:* The LLM might trigger `book_appointment` or `cancel_appointment` without verbal patient consent.
   - *Mitigation:* Multi-flag server-side guardrails (`phone_readback_confirmed`, `action_confirmed`, and utterance sequence verification) inside tool handlers.
4. **Spoken Phone Number Security:**
   - *Risk:* Anyone knowing a patient's phone number can attempt unauthorized cancellation.
   - *Mitigation:* Strict rate-limiting, minimal data disclosure, audit logs with soft cancellations, and prominent user documentation of architectural limitations.

---

## 7. Audit Verdict & Next Step

The project repository is in a clean, well-architected pre-implementation state. Phase 1 (Research & Architecture) is thoroughly documented. Development should not start from Phase 1, but rather proceed directly to **Phase 2: Backend Foundation and Database** upon client sign-off on the core configuration parameters.
