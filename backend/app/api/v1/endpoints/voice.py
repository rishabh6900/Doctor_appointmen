"""WebRTC signaling and voice session REST endpoints."""

import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.voice.session_manager import voice_session_manager
from app.database.session import get_db
from app.voice.interaction_service import VoiceInteractionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice Pipeline"])


class WebRTCOfferRequest(BaseModel):
    sdp: str = Field(..., description="Browser WebRTC Session Description (SDP offer)")
    type: str = Field("offer", description="WebRTC message type ('offer')")
    session_id: Optional[str] = Field(None, description="Optional existing session ID")


class WebRTCAnswerResponse(BaseModel):
    session_id: str
    sdp: str
    type: str = "answer"


@router.post(
    "/offer",
    response_model=WebRTCAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="WebRTC Signaling: Exchange SDP offer for SDP answer",
)
async def handle_webrtc_offer(payload: WebRTCOfferRequest):
    """
    Handle browser WebRTC SDP offer, initialize a Pipecat voice pipeline,
    and return the SDP answer for peer-to-peer real-time audio.
    """
    from app.voice.pipeline import create_voice_pipeline_session

    try:
        session_id = payload.session_id or None
        sdp_answer, session = await create_voice_pipeline_session(
            sdp_offer=payload.sdp,
            session_id=session_id,
        )
        return WebRTCAnswerResponse(
            session_id=session.session_id,
            sdp=sdp_answer,
            type="answer",
        )
    except Exception as exc:
        logger.error(f"Error establishing WebRTC voice session: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to establish WebRTC voice session: {str(exc)}",
        )


@router.post(
    "/sessions/{session_id}/end",
    status_code=status.HTTP_200_OK,
    summary="Terminate an active voice call session",
)
async def end_voice_session(session_id: str):
    """End an active voice session and release pipeline audio resources."""
    session = voice_session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Voice session {session_id} not found.",
        )
    await voice_session_manager.end_session(session_id)
    return {"status": "ended", "session_id": session_id}


@router.get(
    "/sessions",
    status_code=status.HTTP_200_OK,
    summary="List active voice call sessions",
)
def list_voice_sessions():
    """Retrieve all currently active voice sessions."""
    return {"sessions": voice_session_manager.list_active_sessions()}


class VoiceInteractRequest(BaseModel):
    message: str = Field(..., description="Spoken or typed patient message")
    session_id: Optional[str] = Field(None, description="Voice session ID")
    history: Optional[List[Dict[str, str]]] = Field(None, description="Recent conversation turns")


class VoiceInteractResponse(BaseModel):
    session_id: str
    response_text: str
    appointment_updated: bool = False
    tools_called: List[str] = []


@router.post(
    "/interact",
    response_model=VoiceInteractResponse,
    status_code=status.HTTP_200_OK,
    summary="Process conversational voice speech interaction",
)
def voice_interact(payload: VoiceInteractRequest, db: Session = Depends(get_db)):
    """
    Process patient speech input, invoke clinic tools (availability check, booking, cancellation),
    and return receptionist verbal response with real-time UI synchronization flags.
    """
    service = VoiceInteractionService(db)
    result = service.interact(
        message=payload.message,
        session_id=payload.session_id,
        history=payload.history,
    )
    return VoiceInteractResponse(
        session_id=result["session_id"],
        response_text=result["response_text"],
        appointment_updated=result.get("appointment_updated", False),
        tools_called=result.get("tools_called", []),
    )

