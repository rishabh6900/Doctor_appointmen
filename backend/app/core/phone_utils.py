"""Phone number normalization, validation, and speech readback formatting."""

import re
from typing import Optional, Tuple
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat
from app.core.config import settings

# Spoken digit word substitutions (English, doubles/triples, and Hinglish)
WORD_TO_DIGIT = {
    "zero": "0", "oh": "0", "one": "1", "two": "2", "three": "3",
    "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
    "nine": "9",
    "double zero": "00", "double one": "11", "double two": "22",
    "double three": "33", "double four": "44", "double five": "55",
    "double six": "66", "double seven": "77", "double eight": "88",
    "double nine": "99",
    "triple zero": "000", "triple one": "111", "triple two": "222",
    "triple three": "333", "triple four": "444", "triple five": "555",
    "triple six": "666", "triple seven": "777", "triple eight": "888",
    "triple nine": "999",
    # Hinglish spoken digits
    "shunya": "0", "ek": "1", "do": "2", "teen": "3",
    "chaar": "4", "char": "4", "paanch": "5", "panch": "5",
    "chhah": "6", "che": "6", "saat": "7", "aath": "8", "nau": "9",
}


def clean_spoken_phone_input(spoken_text: str) -> str:
    """
    Clean conversational filler words and convert spoken number words into digits.
    Handles 'yeh 7860634479', 'my number is', 'o' vs '0', etc.
    """
    if not spoken_text:
        return ""

    cleaned = spoken_text.lower().strip()

    # Remove common conversational prefixes
    cleaned = re.sub(
        r"^(?:yeh|yeah|yes|yep|mera|my|the)?\s*(?:mobile|phone)?\s*(?:number|no)?\s*(?:is|h)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Replace multi-word phrases first, then single-word digits
    sorted_words = sorted(WORD_TO_DIGIT.items(), key=lambda x: len(x[0]), reverse=True)
    for word, digit in sorted_words:
        cleaned = re.sub(rf"\b{word}\b", digit, cleaned)

    # Replace isolated 'o' or 'O' with '0'
    cleaned = re.sub(r"\bo\b", "0", cleaned, flags=re.IGNORECASE)

    # In a sequence of digits, replace 'o' or 'O' between digits or with spaces with '0'
    cleaned = re.sub(r"(\d)\s*[oO]\s*(\d)", r"\1 0 \2", cleaned)
    cleaned = re.sub(r"(\d)[oO](\d)", r"\g<1>0\g<2>", cleaned)

    return cleaned


def is_phone_correction(spoken_text: str) -> bool:
    """
    Detect if the user is correcting the phone number (e.g., 'it's zero not o', 'no, replace with...').
    """
    if not spoken_text:
        return False
    lower = spoken_text.lower()
    return bool(re.search(r"\b(zero\s+not\s+o|not\s+o|it(?:'s|\s+is)\s+zero|correction|wrong\s+number|correct\s+number|mistake)\b", lower))


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
    cleaned = clean_spoken_phone_input(spoken_text)

    # Extract digits and optional leading plus
    has_plus = cleaned.strip().startswith("+")
    digits_only = re.sub(r"[^\d]", "", cleaned)

    if not digits_only:
        return False, "", "No telephone digits found in speech."

    raw_candidate = f"+{digits_only}" if has_plus else digits_only

    try:
        parsed = phonenumbers.parse(raw_candidate, region)
        # Check both valid number and possible number (to allow demo/test 555 exchange numbers)
        if not (phonenumbers.is_valid_number(parsed) or phonenumbers.is_possible_number(parsed)):
            # If 10 digits given without country code for default region, accept if valid length
            if len(digits_only) == 10 and not has_plus:
                if region == "IN":
                    return True, f"+91{digits_only}", ""
                elif region == "US":
                    return True, f"+1{digits_only}", ""
            return False, "", "The phone number is not a valid recognized telephone number."

        e164_num = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
        return True, e164_num, ""
    except NumberParseException as exc:
        # Fallback for standard 10 digit numbers
        if len(digits_only) == 10 and not has_plus:
            prefix = "+91" if region == "IN" else "+1"
            return True, f"{prefix}{digits_only}", ""
        return False, "", f"Could not parse phone number: {str(exc)}"


def format_phone_digit_by_digit(phone: str) -> str:
    """
    Format phone digits with hyphens between every digit:
    e.g., '+917860634479' -> '7-8-6-0-6-3-4-4-7-9' (national 10 digits)
    or '+15551234567' -> '5-5-5-1-2-3-4-5-6-7'
    """
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) == 12 and digits.startswith("91"):
        national_digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("1"):
        national_digits = digits[1:]
    else:
        national_digits = digits

    return "-".join(list(national_digits))


def generate_phone_confirmation_prompt(phone: str) -> str:
    """
    Generate the standard verbal confirmation prompt:
    'I heard 7-8-6-0-6-3-4-4-7-9. Is that correct?'
    """
    hyphenated = format_phone_digit_by_digit(phone)
    return f"I heard {hyphenated}. Is that correct?"


def format_phone_for_speech(e164_phone: str) -> str:
    """
    Format an E.164 phone number into spaced digit groups for natural TTS readback.
    e.g., '+15551234567' -> '5 5 5, 1 2 3, 4 5 6 7'
    """
    try:
        parsed = phonenumbers.parse(e164_phone, None)
        national = phonenumbers.format_number(parsed, PhoneNumberFormat.NATIONAL)
        digits = re.sub(r"[^\d]", "", national)
        if len(digits) == 10:
            return f"{' '.join(digits[:3])}, {' '.join(digits[3:6])}, {' '.join(digits[6:])}"
        elif len(digits) == 11 and digits.startswith("1"):
            return f"{' '.join(digits[1:4])}, {' '.join(digits[4:7])}, {' '.join(digits[7:])}"
        else:
            return " ".join(digits)
    except Exception:
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
