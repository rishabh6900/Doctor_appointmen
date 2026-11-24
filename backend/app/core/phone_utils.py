"""Phone number normalization, validation, and speech readback formatting."""

import re
from typing import Optional, Tuple
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
from app.core.config import settings

# Spoken digit word substitutions
WORD_TO_DIGIT = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9", "double zero": "00", "double one": "11", "double two": "22",
    "double three": "33", "double four": "44", "double five": "55",
    "double six": "66", "double seven": "77", "double eight": "88",
    "double nine": "99",
}


def normalize_spoken_phone_number(
    spoken_text: str,
    default_region: Optional[str] = None,
) -> Tuple[bool, str, str]:
    """
    Parse and validate a spoken phone number.

    Returns:
        (is_valid, e164_formatted_number, error_message)
    """
    if not spoken_text or not spoken_text.strip():
        return False, "", "Phone number cannot be empty."

    region = default_region or settings.DEFAULT_PHONE_REGION
    cleaned = spoken_text.lower()

    # Replace multi-word phrases first, then single-word digits
    sorted_words = sorted(WORD_TO_DIGIT.items(), key=lambda x: len(x[0]), reverse=True)
    for word, digit in sorted_words:
        cleaned = re.sub(rf"\b{word}\b", digit, cleaned)

    # Extract digits and optional leading plus
    has_plus = cleaned.strip().startswith("+")
    digits_only = re.sub(r"[^\d]", "", cleaned)

    raw_candidate = f"+{digits_only}" if has_plus else digits_only

    try:
        parsed = phonenumbers.parse(raw_candidate, region)
        # Check both valid number and possible number (to allow demo/test 555 exchange numbers)
        if not (phonenumbers.is_valid_number(parsed) or phonenumbers.is_possible_number(parsed)):
            return False, "", "The phone number is not a valid recognized telephone number."

        e164_num = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        return True, e164_num, ""
    except NumberParseException as exc:
        return False, "", f"Could not parse phone number: {str(exc)}"


def format_phone_for_speech(e164_phone: str) -> str:
    """
    Format an E.164 phone number into spaced digit groups for natural TTS readback.
    e.g., '+15551234567' -> '5 5 5, 1 2 3, 4 5 6 7'
    """
    try:
        parsed = phonenumbers.parse(e164_phone, None)
        national = phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL)
        # Extract digits
        digits = re.sub(r"[^\d]", "", national)
        if len(digits) == 10:
            return f"{' '.join(digits[:3])}, {' '.join(digits[3:6])}, {' '.join(digits[6:])}"
        elif len(digits) == 11 and digits.startswith("1"):
            # US with country code
            return f"{' '.join(digits[1:4])}, {' '.join(digits[4:7])}, {' '.join(digits[7:])}"
        else:
            return " ".join(digits)
    except Exception:
        # Fallback to plain spaced digits
        digits = re.sub(r"[^\d]", "", e164_phone)
        return " ".join(digits)


def mask_phone_number(e164_phone: str) -> str:
    """
    Mask phone number for safe display in logs and UI.
    e.g., '+15551234567' -> '+1 (***) ***-4567'
    """
    if not e164_phone or len(e164_phone) < 4:
        return "****"

    last_4 = e164_phone[-4:]
    return f"***-***-{last_4}"
