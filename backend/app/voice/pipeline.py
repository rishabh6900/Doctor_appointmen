"""Pipecat Voice Pipeline Factory for Real-Time Medical Receptionist."""

import asyncio
import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.database.session import SessionLocal
from app.voice.prompts import get_system_prompt
from app.voice.session_manager import VoiceSession, voice_session_manager
from app.voice.conversation_state import conversation_state_manager
from app.voice.tools import (
    VOICE_TOOLS,
    execute_check_doctor_availability,
    execute_book_appointment,
    execute_cancel_appointment,
)
from app.services.availability_service import AvailabilityService

# Pipecat framework imports
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.google.llm import GoogleLLMService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.elevenlabs.stt import ElevenLabsRealtimeSTTService, ElevenLabsSTTService
from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport

logger = logging.getLogger(__name__)


async def create_voice_pipeline_session(
    sdp_offer: str,
    session_id: Optional[str] = None,
) -> Tuple[str, VoiceSession]:
    """
    Construct, wire, and launch a complete Pipecat 1.x voice session.

    Pipeline Audio Flow:
    Browser Mic (WebRTC) -> Silero VAD -> ElevenLabs STT -> Google Gemini LLM (with 3 tools) -> ElevenLabs TTS -> Browser Speaker (WebRTC)
    """
    session = voice_session_manager.create_session(session_id)
    state = conversation_state_manager.get_or_create(session.session_id)
    logger.info(f"[{session.session_id}] Initializing Pipecat voice pipeline session")

    # 1. Initialize WebRTC Peer Connection and generate Answer
    webrtc_conn = SmallWebRTCConnection()
    await webrtc_conn.initialize(sdp=sdp_offer, type="offer")
    answer_dict = webrtc_conn.get_answer()
    if not answer_dict or not isinstance(answer_dict, dict) or "sdp" not in answer_dict:
        logger.error(f"[{session.session_id}] WebRTC answer generation returned invalid payload: {answer_dict}")
        raise RuntimeError("Failed to generate WebRTC SDP answer: SmallWebRTCConnection returned no valid SDP.")
    sdp_answer = str(answer_dict["sdp"])
    logger.info(f"[{session.session_id}] WebRTC SDP answer generated successfully")

    # 2. Configure SmallWebRTCTransport
    transport_params = TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        camera_in_enabled=False,
        camera_out_enabled=False,
    )
    transport = SmallWebRTCTransport(
        webrtc_connection=webrtc_conn,
        params=transport_params,
    )
    session.transport = transport

    # 3. Configure Silero VAD & VADProcessor
    vad = SileroVADAnalyzer(sample_rate=16000)
    vad_processor = VADProcessor(vad_analyzer=vad)
    logger.info(f"[{session.session_id}] Silero VAD analyzer and VADProcessor initialized")

    # 4. Configure ElevenLabs Speech-to-Text (STT) safely
    stt = None
    if settings.ELEVENLABS_API_KEY and not settings.ELEVENLABS_API_KEY.startswith("dummy"):
        try:
            stt = ElevenLabsRealtimeSTTService(
                api_key=settings.ELEVENLABS_API_KEY,
                model="scribe_v2_realtime",
            )
        except Exception as e:
            logger.warning(f"ElevenLabs STT initialization note: {e}")
            stt = None

    # 5. Configure Google Gemini LLM with system prompt & 3 function tools
    db_session: Session = SessionLocal()
    avail_service = AvailabilityService(db_session)
    clinic_today = avail_service.get_clinic_today()

    system_instruction = get_system_prompt(clinic_today)

    llm = GoogleLLMService(
        api_key=settings.GOOGLE_API_KEY or "dummy_key",
        model=settings.GEMINI_MODEL,
        system_instruction=system_instruction,
        tools=VOICE_TOOLS,
    )

    # Tool 1: check_doctor_availability handler
    async def handle_check_availability(function_name, tool_call_id, args, llm_context, result_callback):
        logger.info(f"[{session.session_id}] Voice Tool Execution: check_doctor_availability({args})")
        doc_db = SessionLocal()
        try:
            result = execute_check_doctor_availability(
                db=doc_db,
                doctor_name=args.get("doctor_name"),
                speciality=args.get("speciality"),
                appointment_date=args.get("appointment_date"),
            )
            state.last_tool_result = result
            session.touch()
            if result.get("status") == "cancelled":
                state.cancellation_confirmation = True
                state.cancelled_appointment_id = result.get("appointment_id")
            await result_callback(result)
        finally:
            doc_db.close()

    # Tool 2: book_appointment handler
    async def handle_book_appointment(function_name, tool_call_id, args, llm_context, result_callback):
        logger.info(f"[{session.session_id}] Voice Tool Execution: book_appointment({args})")
        doc_db = SessionLocal()
        try:
            result = execute_book_appointment(
                db=doc_db,
                patient_phone_number=args.get("patient_phone_number", ""),
                doctor_id=args.get("doctor_id", 0),
                appointment_date=args.get("appointment_date", ""),
                appointment_time=args.get("appointment_time", ""),
                patient_name=args.get("patient_name"),
                phone_readback_confirmed=args.get("phone_readback_confirmed", False),
                action_confirmed=args.get("action_confirmed", False),
            )
            session.touch()
            if result.get("status") == "confirmed":
                session.patient_phone = result.get("patient_phone_number")
                state.patient_phone = result.get("patient_phone_number")
                state.phone_confirmed = True
                state.booking_confirmation = True
                state.booked_appointment_id = result.get("booking_id")
            await result_callback(result)
        finally:
            doc_db.close()

    # Tool 3: cancel_appointment handler
    async def handle_cancel_appointment(function_name, tool_call_id, args, llm_context, result_callback):
        logger.info(f"[{session.session_id}] Voice Tool Execution: cancel_appointment({args})")
        doc_db = SessionLocal()
        try:
            result = execute_cancel_appointment(
                db=doc_db,
                patient_phone_number=args.get("patient_phone_number", ""),
                appointment_id=args.get("appointment_id"),
                phone_readback_confirmed=args.get("phone_readback_confirmed", False),
                action_confirmed=args.get("action_confirmed", False),
            )
            session.touch()
            if result.get("status") == "cancelled":
                state.cancellation_confirmation = True
                state.cancelled_appointment_id = result.get("appointment_id")
            await result_callback(result)
        finally:
            doc_db.close()

    llm.register_function("check_doctor_availability", handle_check_availability, cancel_on_interruption=False)
    llm.register_function("book_appointment", handle_book_appointment, cancel_on_interruption=False)
    llm.register_function("cancel_appointment", handle_cancel_appointment, cancel_on_interruption=False)

    # 6. Configure ElevenLabs Text-to-Speech (TTS) safely
    tts = None
    if settings.ELEVENLABS_API_KEY and not settings.ELEVENLABS_API_KEY.startswith("dummy"):
        try:
            tts = ElevenLabsTTSService(
                api_key=settings.ELEVENLABS_API_KEY,
                voice_id=settings.ELEVENLABS_VOICE_ID,
                model=settings.ELEVENLABS_MODEL_ID,
            )
        except Exception as e:
            logger.warning(f"ElevenLabs TTS initialization note: {e}")
            tts = None

    # 7. Build Pipeline
    processors = [transport.input(), vad_processor]
    if stt:
        processors.append(stt)
        logger.info(f"[{session.session_id}] ElevenLabs STT service connected to pipeline")
    else:
        logger.info(f"[{session.session_id}] Running pipeline with browser client-side transcription bridge")

    processors.append(llm)

    if tts:
        processors.append(tts)
        logger.info(f"[{session.session_id}] ElevenLabs TTS service connected to pipeline")
    else:
        logger.info(f"[{session.session_id}] Running pipeline with client-side speech synthesis bridge")

    processors.append(transport.output())

    pipeline = Pipeline(processors)
    session.pipeline = pipeline

    # 8. Start Background Runner Task
    task = PipelineTask(pipeline, params=PipelineParams(allow_interruptions=True))
    runner = PipelineRunner()

    async def run_pipeline():
        try:
            session.status = "active"
            logger.info(f"Starting voice pipeline runner for {session.session_id}")
            await runner.run(task)
        except asyncio.CancelledError:
            logger.info(f"Voice pipeline cancelled for {session.session_id}")
        except Exception as exc:
            logger.error(f"Voice pipeline runtime error: {exc}", exc_info=True)
            session.status = "failed"
        finally:
            db_session.close()

    session.runner_task = asyncio.create_task(run_pipeline())

    return sdp_answer, session
