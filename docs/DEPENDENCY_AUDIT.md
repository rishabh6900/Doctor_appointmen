# Backend Dependency Audit

## Overview
All dependencies in `backend/requirements.txt` are pinned to production-ready version constraints. No unused or bloated libraries are present.

---

## Dependency Classification

| Package | Version Constraint | Category | Justification |
| :--- | :--- | :--- | :--- |
| `fastapi` | `>=0.115.0,<1.0.0` | Core | REST API & WebSocket routing framework |
| `uvicorn[standard]` | `>=0.32.0,<1.0.0` | Core | High-performance ASGI production server |
| `sqlalchemy` | `>=2.0.35,<3.0.0` | Core | Database ORM and query construction |
| `pydantic` | `>=2.9.0,<3.0.0` | Core | Request/response schema validation |
| `pydantic-settings` | `>=2.5.0,<3.0.0` | Core | Typed application configuration management |
| `alembic` | `>=1.13.0,<2.0.0` | Database | Schema migrations |
| `python-dotenv` | `>=1.0.1,<2.0.0` | Config | `.env` file environment variable loading |
| `phonenumbers` | `>=8.13.45,<9.0.0` | Utility | E.164 phone normalization and validation |
| `httpx` | `>=0.27.2,<1.0.0` | Network | HTTP client for external service calls |
| `pytz` | `>=2024.2` | Core | Timezone normalization (America/New_York / Asia/Kolkata) |
| `pipecat-ai` | `>=1.17.0` | Voice | Central real-time voice orchestration pipeline |
| `pipecat-ai[webrtc]` | `>=1.17.0` | Voice | SmallWebRTC transport and peer connection |
| `pipecat-ai[google]` | `>=1.17.0` | AI / LLM | Gemini streaming LLM integration |
| `pipecat-ai[elevenlabs]` | `>=1.17.0` | Speech | ElevenLabs STT and TTS streaming services |
| `aiortc` | `>=1.16.0` | WebRTC | Python asyncio WebRTC and ORTC implementation |
| `google-genai` | `>=3.6.0` | AI / LLM | Official Google Gemini SDK |
| `silero-vad` | `>=5.1.2` | Audio | Voice activity and silence detection |
| `websockets` | `>=13.1` | Network | Real-time WebSocket connection handling |
| `pytest` | `>=8.3.0,<9.0.0` | Testing | Automated test suite execution |
| `pytest-asyncio` | `>=0.24.0,<1.0.0` | Testing | Async test execution support |
