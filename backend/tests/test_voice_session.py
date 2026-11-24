"""Tests for VoiceSessionManager and voice session lifecycle."""

import pytest
from app.voice.session_manager import VoiceSessionManager, VoiceSession


def test_voice_session_creation_and_retrieval():
    """Test creating and retrieving voice sessions."""
    manager = VoiceSessionManager()
    session = manager.create_session("test-session-123")
    assert session.session_id == "test-session-123"
    assert session.status == "connecting"

    retrieved = manager.get_session("test-session-123")
    assert retrieved is not None
    assert retrieved.session_id == "test-session-123"


def test_voice_session_listing_and_ending():
    """Test listing active voice sessions and ending a session."""
    manager = VoiceSessionManager()
    s1 = manager.create_session("sess-1")
    s2 = manager.create_session("sess-2")

    active = manager.list_active_sessions()
    assert len(active) == 2
    ids = {s["session_id"] for s in active}
    assert ids == {"sess-1", "sess-2"}


@pytest.mark.asyncio
async def test_end_session():
    """Test async session termination."""
    manager = VoiceSessionManager()
    manager.create_session("sess-term")
    assert manager.get_session("sess-term") is not None

    await manager.end_session("sess-term")
    assert manager.get_session("sess-term") is None
