# Voice Pipeline Flow & Audio Lifecycle

## End-to-End Pipeline Architecture

```
Caller Microphone (Browser)
      │
      ▼ (WebRTC MediaStream Audio 16kHz)
SmallWebRTCTransport (Input Processor)
      │
      ▼ (Audio Frames)
Silero VAD (VADProcessor - Voice Activity Detection)
      │
      ▼ (Speech Audio Chunks)
ElevenLabs STT (Realtime STT Service - scribe_v2_realtime)
      │
      ▼ (Text Transcript Frame)
Conversation State Manager & FSMEngine
      │
      ▼ (State-Enriched Clinical Context)
Google Gemini LLM Service (gemini-3.5-flash-lite)
      │  ├── check_doctor_availability
      │  ├── book_appointment
      │  └── cancel_appointment
      ▼ (LLM Text Tokens Frame)
ElevenLabs TTS (Text-to-Speech Service - eleven_turbo_v2_5)
      │
      ▼ (Synthesized Audio Frames)
SmallWebRTCTransport (Output Processor)
      │
      ▼ (WebRTC Peer Audio Track)
Browser Speaker Output
```

---

## Tool Calling Flow

1. **check_doctor_availability:**
   - Queries database for active doctor schedules and reserved appointments.
   - Computes open 30-minute intervals.
   - Never hallucinates dates or unavailable doctors.

2. **book_appointment:**
   - Re-verifies slot availability to prevent double-booking.
   - Enforces two-stage confirmation: digit-by-digit phone number readback + caller confirmation.
   - Atomic database transaction creates confirmed booking.

3. **cancel_appointment:**
   - Locates appointment matching caller phone number.
   - Reads appointment details back to caller and requests explicit confirmation.
   - Updates status to `cancelled` and frees the slot.
