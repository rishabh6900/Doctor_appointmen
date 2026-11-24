"""Tests for phone number normalization, speech formatting, and masking."""

from app.core.phone_utils import (
    normalize_spoken_phone_number,
    format_phone_for_speech,
    mask_phone_number,
)


def test_normalize_standard_numeric_phone():
    """Test standard 10-digit US number."""
    valid, e164, err = normalize_spoken_phone_number("5551234567", default_region="US")
    assert valid is True
    assert e164 == "+15551234567"
    assert err == ""


def test_normalize_spoken_words():
    """Test words spoken like 'five five five one two three four five six seven'."""
    spoken = "five five five one two three four five six seven"
    valid, e164, err = normalize_spoken_phone_number(spoken, default_region="US")
    assert valid is True
    assert e164 == "+15551234567"


def test_normalize_spoken_with_oh_and_double():
    """Test words containing 'oh' and 'double five'."""
    spoken = "five five five oh double five four three two one"
    valid, e164, err = normalize_spoken_phone_number(spoken, default_region="US")
    assert valid is True
    assert e164 == "+15550554321"


def test_normalize_indian_phone_number():
    """Test Indian 10-digit mobile number."""
    valid, e164, err = normalize_spoken_phone_number("9876543210", default_region="IN")
    assert valid is True
    assert e164 == "+919876543210"


def test_normalize_invalid_phone():
    """Test invalid or truncated digits."""
    valid, e164, err = normalize_spoken_phone_number("123")
    assert valid is False
    assert "not a valid" in err.lower() or "too short" in err.lower()


def test_format_phone_for_speech():
    """Test natural TTS readback grouping."""
    formatted = format_phone_for_speech("+15551234567")
    assert formatted == "5 5 5, 1 2 3, 4 5 6 7"


def test_mask_phone_number():
    """Test privacy masking displays only the last 4 digits."""
    masked = mask_phone_number("+15551234567")
    assert masked == "***-***-4567"
