"""Voice Session Management and WebRTC Lifecycle."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class VoiceSession:
    """Represents an active real-time conversational call session."""

    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.created_at: datetime = datetime.now(timezone.utc)
        self.last_active: datetime = datetime.now(timezone.utc)
        self.status: str = "connecting"  # connecting, active, ended, failed
        self.transport: Any = None
        self.pipeline: Any = None
        self.runner_task: Any = None
        self.transcript: list = []
        self.patient_phone: Optional[str] = None
        self.last_readback_phone: Optional[str] = None
        self.phone_readback_confirmed: bool = False
        self.action_confirmed: bool = False

    def touch(self):
        """Update last active timestamp."""
        self.last_active = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize session state for API reporting."""
        duration_sec = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return {
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "duration_seconds": round(duration_sec, 1),
            "patient_phone": self.patient_phone,
            "transcript_count": len(self.transcript),
        }


class VoiceSessionManager:
    """Singleton registry tracking active peer-to-peer Pipecat WebRTC sessions."""

    def __init__(self):
        self.sessions: Dict[str, VoiceSession] = {}

    def create_session(self, session_id: Optional[str] = None) -> VoiceSession:
        """Create and register a new voice session."""
        sid = session_id or str(uuid.uuid4())
        session = VoiceSession(sid)
        self.sessions[sid] = session
        logger.info(f"Created voice session: {sid}")
        return session

    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Retrieve active session by ID."""
        return self.sessions.get(session_id)

    def get_or_create_session(self, session_id: Optional[str] = None) -> VoiceSession:
        """Retrieve existing session or instantiate a new one."""
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.touch()
            return session
        return self.create_session(session_id)

    async def end_session(self, session_id: str):
        """Cleanly terminate and unregister a voice session."""
        session = self.sessions.get(session_id)
        if not session:
            return

        session.status = "ended"
        logger.info(f"Ending voice session: {session_id}")

        if session.runner_task and not session.runner_task.done():
            session.runner_task.cancel()

        self.sessions.pop(session_id, None)
        try:
            from app.voice.conversation_state import conversation_state_manager
            conversation_state_manager.remove(session_id)
        except Exception:
            pass

    def list_active_sessions(self) -> list:
        """List summary of active call sessions."""
        return [s.to_dict() for s in self.sessions.values()]


# Global singleton instance
voice_session_manager = VoiceSessionManager()
