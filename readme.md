# CarePoint Health — AI Voice-Based Doctor Appointment Booking System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Pipecat](https://img.shields.io/badge/Pipecat-1.17+-792EE5.svg)](https://github.com/pipecat-ai/pipecat)
[![Google Gemini](https://img.shields.io/badge/LLM-Gemini_Flash-4285F4.svg)](https://ai.google.dev/)
[![ElevenLabs](https://img.shields.io/badge/Voice-ElevenLabs_STT%2FTTS-black.svg)](https://elevenlabs.io/)
[![React](https://img.shields.io/badge/Frontend-React_19_+_TypeScript-61DAFB.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-51_Passed-brightgreen.svg)](https://pytest.org/)

An enterprise-grade, real-time conversational AI medical receptionist system for **CarePoint Health Medical Clinic**. Patients can check physician availability, book consultations, and cancel appointments using natural voice over WebRTC. The system provides zero double-booking concurrency guarantees, mandatory verbal confirmation guardrails, real-time WebSocket dashboard sync, and live frequency waveform visualization.

---

## Table of Contents

1. [Executive Summary & Architecture](#executive-summary--architecture)
2. [Technology Stack](#technology-stack)
3. [Key Features](#key-features)
4. [Voice Pipeline & Safety Guardrails](#voice-pipeline--safety-guardrails)
5. [Project Structure](#project-structure)
6. [Prerequisites & Environment Configuration](#prerequisites--environment-configuration)
7. [Step-by-Step Local Setup & Execution](#step-by-step-local-setup--execution)
8. [API Documentation & WebSocket Endpoints](#api-documentation--websocket-endpoints)
9. [Automated Testing & Quality Verification](#automated-testing--quality-verification)
10. [Database Schema & Concurrency Design](#database-schema--concurrency-design)
11. [Troubleshooting & Common Questions](#troubleshooting--common-questions)

---

## Executive Summary & Architecture

```
                       ┌────────────────────────────────────────────────────────┐
                       │                   PATIENT BROWSER                      │
                       │   React + TypeScript + Tailwind + Web Audio Analyser   │
                       └──────────────┬────────────────────────▲────────────────┘
                                      │                        │
                    WebRTC SDP Offer / Answer       WebSocket Live Events
                   (Browser Mic Audio Stream)      (appointment_booked/cancelled)
                                      │                        │
                                      ▼                        │
┌───────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI BACKEND SERVICE                             │
│                                                                               │
│  ┌───────────────────────┐   ┌────────────────────────┐   ┌────────────────┐ │
│  │ WebRTC Voice Pipeline │   │ WebSocket Event Engine │   │ REST API /v1   │ │
│  │ (SmallWebRTC Transport│   │  (Active Client Broad- │   │ - Doctors      │ │
│  │  + Session Manager)   │   │   casting with Lock)   │   │ - Availability │ │
│  └───────────┬───────────┘   └───────────▲────────────┘   │ - Appointments │ │
│              │                           │                │ - Health       │ │
│              ▼                           │                └────────┬───────┘ │
│  ┌───────────────────────┐               │                         │         │
│  │ Pipecat Pipeline 1.x  │               │                         │         │
│  │ - Silero VAD          │               │                         │         │
│  │ - ElevenLabs STT      │               │                         │         │
│  │ - Google Gemini Flash │               │                         │         │
│  │ - ElevenLabs TTS      │               │                         │         │
│  └───────────┬───────────┘               │                         │         │
│              │ Function Calling          │ Broadcast Triggers      │         │
│              ▼                           │                         ▼         │
│  ┌───────────────────────────────────────┴─────────────────────────────────┐ │
│  │          APPOINTMENT SERVICE & BUSINESS LOGIC LAYER                     │ │
│  │  - Phone Normalization & Speech Readback Formatting                     │ │
│  │  - Mandatory Verbal Readback & Action Confirmation Guards               │ │
│  │  - Two-Stage Cancellation with Disambiguation Engine                    │ │
│  │  - Dynamic Discrete 30-min Slot Generator & Nearby Alternatives         │ │
│  └───────────────────────────────────────┬─────────────────────────────────┘ │
│                                          │                                   │
│                                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                SQLITE WITH WAL MODE & REPOSITORIES                      │ │
│  │  - Partial Unique Index: uq_active_slot (doctor_id, date, time)         │ │
│  │    WHERE status = 'confirmed'                                           │ │
│  │  - Cascading Foreign Keys & Strict ACID Transaction Isolation           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Layer | Component | Technology Used | Version / Specification |
|---|---|---|---|
| **Voice Framework** | Real-time Orchestration | **Pipecat AI** | `>=1.17.0` |
| **STT** | Speech-to-Text | **ElevenLabs Real-time STT** | Single-channel PCM 16kHz |
| **LLM** | Conversational Reasoning | **Google Gemini Flash** | `gemini-2.5-flash` via `google-genai` |
| **TTS** | Speech Synthesis | **ElevenLabs Turbo** | `eleven_turbo_v2_5` |
| **VAD** | Voice Activity Detection | **Silero VAD** | `silero-vad>=5.1.2` |
| **WebRTC Transport** | Audio Transport | **SmallWebRTCTransport** / `aiortc` | ICE, SDP, Datachannel |
| **Backend Framework** | Web / REST / WebSocket | **FastAPI** | `>=0.115.0` + `uvicorn` |
| **Database & ORM** | Relational Persistence | **SQLite WAL Mode** + **SQLAlchemy** | `>=2.0.35` (PostgreSQL ready) |
| **Frontend** | Clinical Dashboard UI | **React 19**, **Vite**, **TypeScript** | Strict typings, zero warnings |
| **Styling & Icons** | Clinical Healthcare Design | **Tailwind CSS**, **Lucide React** | Medical teal & slate design |
| **Testing** | Automated Quality Suite | **Pytest**, **pytest-asyncio** | 51 passing tests (unit, e2e, ws) |

---

## Key Features

1. **Conversational Spoken Booking:**
   - Understands colloquial dates (*"tomorrow"*, *"next Monday"*), doctor specialties (*"Cardiologist"*, *"Skin specialist"*), and natural telephone digits (*"nine eight seven double six"*).
2. **Strict Server-Side Safety Guards:**
   - **Phone Readback Guard:** Voice tool execution refuses booking unless `phone_readback_confirmed=True`.
   - **Action Confirmation Guard:** Refuses state alteration unless the patient explicitly verifies the exact appointment details (`action_confirmed=True`).
   - **Emergency Boundary:** Detects medical emergency words and immediately instructs patients to call **112 / 911** or go to an emergency room.
3. **Zero Double-Booking Concurrency Engine:**
   - Backed by an atomic partial unique index on `(doctor_id, appointment_date, appointment_time) WHERE status = 'confirmed'`.
   - Tested under high-contention parallel multi-threading: exactly 1 booking succeeds; all 9 concurrent requests fail gracefully with alternative suggestions.
4. **Two-Stage Spoken Cancellation:**
   - Stage 1: Disambiguates between multiple active appointments for a phone number.
   - Stage 2: Requests explicit patient confirmation before executing soft cancellation (`status='cancelled'`).
5. **Real-Time Clinical Dashboard:**
   - Instant WebSocket sync across all open browsers on `appointment_booked` or `appointment_cancelled`.
   - Web Audio API canvas visualizer displaying real-time speech oscillations during conversation.
   - Live conversational transcript distinguishing Patient speech, Assistant speech, and Tool execution.

---

## Voice Pipeline & Safety Guardrails

### Autonomous Tools Registered with Gemini
The assistant interacts with the clinic database using three function calling schemas:

1. `check_doctor_availability(doctor_name, speciality, appointment_date)`:
   - Scans 30-minute consultation windows across matching physicians and returns unbooked slots.
2. `book_appointment(patient_phone_number, doctor_id, appointment_date, appointment_time, patient_name, phone_readback_confirmed, action_confirmed)`:
   - Performs atomic validation, normalizes phone numbers to E.164, and records confirmation.
3. `cancel_appointment(patient_phone_number, appointment_id, phone_readback_confirmed, action_confirmed)`:
   - Finds patient reservations and safely processes verified cancellation.

---

## Project Structure

```
voice-based doctor appointmen/
├── .env                                # Local environment secrets & config
├── .env.example                        # Template environment configuration
├── appointments.db                     # SQLite database (WAL mode enabled)
├── readme.md                           # Master system documentation
├── Voice_Appointment_System_Phase1...   # Specification & research PDF
│
├── backend/                            # FastAPI Python Backend
│   ├── requirements.txt                # Pinned production dependencies
│   ├── app/
│   │   ├── main.py                     # App lifespan, CORS, router mounting
│   │   ├── api/v1/
│   │   │   ├── router.py               # Aggregated API v1 endpoints
│   │   │   └── endpoints/
│   │   │       ├── health.py           # Health probe (/health)
│   │   │       ├── doctors.py          # Physician directory & specialty routes
│   │   │       ├── availability.py     # Slot availability calculation endpoints
│   │   │       ├── appointments.py     # REST booking, listing, & cancellation
│   │   │       ├── dashboard.py        # Real-time statistics aggregation
│   │   │       ├── voice.py            # WebRTC signaling (SDP offer/answer)
│   │   │       └── events_ws.py        # WebSocket real-time event broadcaster
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic BaseSettings & timezone parser
│   │   │   ├── phone_utils.py          # E.164 normalization & speech formatters
│   │   │   └── websocket_manager.py    # Thread-safe WebSocket ConnectionManager
│   │   ├── database/
│   │   │   ├── session.py              # Engine creation, PRAGMA WAL, sessionmaker
│   │   │   └── seed.py                 # Idempotent database seeder (8 doctors, 96 windows)
│   │   ├── models/                     # SQLAlchemy declarative models
│   │   │   ├── doctor.py
│   │   │   ├── availability.py
│   │   │   └── appointment.py
│   │   ├── repositories/               # Data access abstraction layer
│   │   │   ├── doctor_repository.py
│   │   │   └── appointment_repository.py
│   │   ├── schemas/                    # Pydantic input/output validation models
│   │   ├── services/                   # Core business logic
│   │   │   ├── availability_service.py # Slot generation & alternatives
│   │   │   └── appointment_service.py  # Atomic booking & cancellation logic
│   │   └── voice/                      # Pipecat & AI integration stack
│   │       ├── prompts.py              # Receptionist system prompt & safety boundaries
│   │       ├── session_manager.py      # WebRTC call session registry
│   │       ├── pipeline.py             # SmallWebRTC, ElevenLabs, Gemini, Silero pipeline
│   │       └── tools/                  # Function calling tools
│   │           ├── availability_tool.py
│   │           ├── booking_tool.py
│   │           └── cancellation_tool.py
│   ├── scripts/
│   │   └── verify_backend.py           # Verification script for live server endpoints
│   └── tests/                          # 51 automated Pytest suites
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_models.py
│       ├── test_seed.py
│       ├── test_phone_utils.py
│       ├── test_availability_service.py
│       ├── test_appointment_service.py
│       ├── test_concurrency.py         # 10-thread parallel booking stress test
│       ├── test_doctors_api.py
│       ├── test_appointments_api.py
│       ├── test_voice_tools.py
│       ├── test_voice_session.py
│       ├── test_voice_signaling.py
│       ├── test_websocket_events.py    # Real-time WebSocket broadcasting test
│       └── test_e2e_voice_flow.py      # End-to-end voice tool workflow test
│
├── frontend/                           # React 19 + TypeScript + Vite UI
│   ├── package.json
│   ├── vite.config.ts                  # Reverse proxy configurations (/api, /health)
│   ├── tailwind.config.js              # Clinical medical color system
│   └── src/
│       ├── types/index.ts              # Strongly-typed data definitions
│       ├── services/
│       │   ├── api.ts                  # Typed REST API & WebRTC signaling client
│       │   └── websocket.ts            # Auto-reconnecting real-time WebSocket client
│       ├── components/
│       │   ├── Navbar.tsx              # Navigation & Call trigger
│       │   ├── StatsOverview.tsx       # KPI banner & metrics
│       │   ├── DoctorDirectory.tsx     # Filterable physician directory
│       │   ├── AppointmentsTable.tsx   # Appointments ledger & cancellation
│       │   ├── AvailabilityViewer.tsx  # Dynamic slot availability viewer
│       │   ├── AudioWaveform.tsx       # Web Audio API canvas frequency visualizer
│       │   └── VoiceCallModal.tsx      # Real-time WebRTC audio call modal
│       ├── App.tsx                     # Main layout & state coordinator
│       └── index.css                   # Tailwind entrypoint
│
└── docs/                               # Architecture & audit records
    ├── REPOSITORY_AUDIT.md
    ├── IMPLEMENTATION_STATUS.md
    ├── GAP_ANALYSIS.md
    └── ENGINEERING_DECISIONS.md
```

---

## Prerequisites & Environment Configuration

### Required Runtimes
- **Python**: Version `3.12+`
- **Node.js**: Version `18.0+` (v20+ recommended)
- **Package Managers**: `pip` and `npm`

### Environment File Setup
Create or update `.env` in the project root:

```ini
# Application Core
PROJECT_NAME="CarePoint Health Medical Clinic"
ENVIRONMENT="development"
DEBUG=true
API_V1_PREFIX="/api/v1"

# Clinic Configuration
CLINIC_NAME="CarePoint Health Medical Clinic"
CLINIC_TIMEZONE="Asia/Kolkata"
DEFAULT_PHONE_REGION="IN"
CLINIC_PHONE="+1-800-555-0199"
CLINIC_OPEN_TIME="09:00"
CLINIC_CLOSE_TIME="17:00"
DEFAULT_SLOT_DURATION_MIN=30

# Database Configuration
DATABASE_URL="sqlite:///./appointments.db"

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:3000","http://127.0.0.1:5173"]

# AI Voice Provider API Keys
GOOGLE_API_KEY="your-google-gemini-api-key"
GEMINI_MODEL="gemini-2.5-flash"
ELEVENLABS_API_KEY="your-elevenlabs-api-key"
ELEVENLABS_VOICE_ID="21m00Tcm4TlvDq8ikWAM"
ELEVENLABS_MODEL_ID="eleven_turbo_v2_5"
```

---

## Step-by-Step Local Setup & Execution

### 1. Backend Installation & Startup

Open a terminal in the root directory:

```powershell
# 1. Install backend dependencies
pip install -r backend/requirements.txt

# 2. Run the FastAPI development server
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend starts at **http://127.0.0.1:8000**:
- Swagger UI Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Frontend Installation & Startup

Open a second terminal:

```powershell
# 1. Navigate to the frontend directory
cd frontend

# 2. Install dependencies (if not already done)
npm install

# 3. Start Vite development server
npm run dev
```

Open your browser at:
👉 **http://localhost:5173**

---

## API Documentation & WebSocket Endpoints

### REST Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Application status and environment probe |
| `GET` | `/api/v1/doctors` | List all doctors (supports `?speciality=` filter) |
| `GET` | `/api/v1/doctors/{id}` | Retrieve specific doctor profile |
| `GET` | `/api/v1/specialities` | List all unique specialties |
| `GET` | `/api/v1/availability` | Calculate 30-min available slots by date & physician |
| `GET` | `/api/v1/appointments` | Query appointments with pagination and filters |
| `POST` | `/api/v1/appointments` | Book appointment with server guard checks |
| `POST` | `/api/v1/appointments/{id}/cancel` | Cancel an existing reservation |
| `GET` | `/api/v1/dashboard/stats` | Clinic KPI counts (doctors, confirmed, cancelled) |
| `POST` | `/api/v1/voice/offer` | WebRTC SDP negotiation for Spoken Voice session |
| `POST` | `/api/v1/voice/sessions/{id}/end` | Terminate active WebRTC audio session |

### WebSocket Live Stream
- **URL:** `ws://127.0.0.1:8000/api/v1/ws/events`
- **Payload Events:**
  - `appointment_booked`: Broadcast when an appointment is booked via voice or dashboard.
  - `appointment_cancelled`: Broadcast when an appointment is cancelled, immediately releasing slots.

---

## Automated Testing & Quality Verification

Run the complete 51-test suite:

```powershell
pytest backend/tests
```

### Coverage Highlights:
- **`test_concurrency.py`**: 10 simultaneous threads attempt to book the exact same slot. Exactly 1 transaction succeeds; 9 receive typed `SLOT_TAKEN` conflicts.
- **`test_e2e_voice_flow.py`**: Full spoken tool conversation verifying discovery, guard refusal, phone word parsing, conflict recovery, cancellation, and slot release.
- **`test_websocket_events.py`**: Verifies real-time event broadcasting on client connections.
- **`test_phone_utils.py`**: Spoken word normalization (`"five five five"` -> `555`), readback formatting, and masking (`***-***-4567`).

---

## Database Schema & Concurrency Design

### Relational Schema (SQLite WAL Mode)

```sql
CREATE TABLE doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(120) NOT NULL,
    speciality VARCHAR(80) NOT NULL,
    experience_years INTEGER NOT NULL DEFAULT 1,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT 1
);

CREATE TABLE availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    slot_duration_min INTEGER NOT NULL DEFAULT 30,
    availability_status VARCHAR(20) NOT NULL DEFAULT 'available'
);

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doctor_id INTEGER NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
    patient_name VARCHAR(120),
    patient_phone_number VARCHAR(32) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    notes TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Concurrency protection: guarantees zero double-booking at database engine level
CREATE UNIQUE INDEX uq_active_slot ON appointments (doctor_id, appointment_date, appointment_time)
WHERE status = 'confirmed';
```

---

## Troubleshooting & Common Questions

1. **"Audio not working or call fails immediately"**
   - Ensure you granted microphone permissions in your browser.
   - Verify `GOOGLE_API_KEY` and `ELEVENLABS_API_KEY` are valid and present in `.env`.
   - Ensure the backend is reachable at `http://127.0.0.1:8000`.

2. **"UnknownTimeZoneError on Windows"**
   - The application automatically normalizes Windows timezone strings (e.g., `"India Standard Time"`) to standard IANA identifiers (`"Asia/Kolkata"`). If configuring manually, prefer IANA names in `.env`.

3. **"Can I deploy with PostgreSQL instead of SQLite?"**
   - Yes. The SQLAlchemy models and transactional queries are compatible with PostgreSQL. Change `DATABASE_URL="postgresql://user:pass@host:5432/db"` in `.env`.

---

## License & Support
Developed for **CarePoint Health Medical Clinic**. Built using Pipecat AI, Google Gemini, ElevenLabs, and FastAPI.
