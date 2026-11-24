# Architectural Decisions: LangChain & LangGraph Evaluation

## Context & Objectives
The AI Voice-Based Doctor Appointment Booking System requires real-time, low-latency (< 800ms) voice interaction, deterministic clinical state tracking (doctor selection, 30-min slot availability, digit-by-digit phone confirmation), and zero hallucination of clinical schedules.

---

## Evaluation of Evaluated Options

### Option A: Pure Python FSM + Pipecat (Selected & Recommended)
* **Architecture:** Pipecat 1.x audio transport + Silero VAD + ElevenLabs STT/TTS + Gemini 3.5 Flash Lite + Deterministic Python FSM (`FSMEngine`) + SQLite WAL.
* **Turn Latency:** ~400–600ms (fastest).
* **Complexity:** Low; pure typed Python data structures (`ConversationState`).
* **Tool Calling:** Native JSON schema directly compatible with Pipecat and Gemini.
* **Why Selected:** Meets all non-negotiable client requirements with zero framework overhead, lowest latency, and no dependency conflicts.

### Option B: Pipecat + LangChain Core + Gemini + Python FSM
* **Turn Latency:** ~600–850ms.
* **Findings:** `ChatGoogleGenerativeAI` adds an unnecessary wrapper around the native `google-genai` SDK and cannot stream raw audio frames through Pipecat processors. `ChatPromptTemplate` adds unnecessary abstraction over existing typed templates.
* **Why Rejected:** Introduces ~35MB+ of dependencies and serialization latency without functional benefit.

### Option C: Pipecat + LangGraph StateGraph
* **Turn Latency:** ~650–900ms.
* **Findings:** LangGraph is designed for multi-agent DAGs and durable checkpointing. For a single-call clinical receptionist, LangGraph's turn serialization and state migration overhead add 50–120ms per turn without adding capabilities beyond what `FSMEngine` provides in < 5ms.
* **Why Rejected:** Violates the sub-800ms conversational turn budget and risks dual-state synchronization issues with Pipecat's internal pipeline state.

---

## Final Decision
Maintain **Option A**: Native Pipecat voice pipeline with deterministic pure Python FSM.
