"""Deterministic Date and Time Processing Service for Clinic Voice Booking."""

import re
from datetime import date, datetime, time, timedelta
from typing import Optional, Tuple, Dict, Any
import pytz

from app.core.config import settings


class DateTimeService:
    """Manages timezone-aware date/time calculations, relative NLP parsing, and ISO normalization."""

    def __init__(self, timezone_str: Optional[str] = None):
        tz_name = timezone_str or settings.iana_timezone
        try:
            self.tz = pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            self.tz = pytz.timezone("Asia/Kolkata")

    def get_clinic_now(self) -> datetime:
        """Current timestamp in clinic timezone."""
        return datetime.now(self.tz)

    def get_clinic_today(self) -> date:
        """Current calendar date in clinic timezone."""
        return self.get_clinic_now().date()

    def parse_relative_or_explicit_date(self, text: str) -> Tuple[Optional[date], Optional[str]]:
        """
        Extract and normalize date from user speech.
        
        Returns:
            (parsed_date, error_message)
        """
        if not text:
            return None, None

        cleaned = text.lower().strip()
        clinic_today = self.get_clinic_today()

        # 1. Direct relative keywords
        if "day after tomorrow" in cleaned:
            return clinic_today + timedelta(days=2), None
        if "tomorrow" in cleaned:
            return clinic_today + timedelta(days=1), None
        if "today" in cleaned:
            return clinic_today, None

        # 2. ISO format YYYY-MM-DD
        iso_match = re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", cleaned)
        if iso_match:
            try:
                y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
                candidate = date(y, m, d)
                if candidate < clinic_today:
                    return None, f"The date {candidate.isoformat()} is in the past. Today is {clinic_today.isoformat()}."
                return candidate, None
            except ValueError:
                pass

        # 3. Day of week (e.g., 'this friday', 'next monday', 'wednesday')
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        for day_name, day_idx in weekdays.items():
            if re.search(rf"\b{day_name}\b", cleaned):
                current_weekday = clinic_today.weekday()
                days_ahead = (day_idx - current_weekday) % 7
                if "next" in cleaned:
                    days_ahead += 7
                elif days_ahead == 0:
                    # If user asks for today's weekday without saying 'next'
                    days_ahead = 7 if "next" in cleaned else 0
                candidate = clinic_today + timedelta(days=days_ahead)
                return candidate, None

        # 4. Month Day (e.g., 'November 25', '25th of November', 'Nov 25th')
        months = {
            "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
            "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
            "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9,
            "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12
        }
        for month_name, month_num in months.items():
            # Matches 'November 25' or '25th November' or 'Nov 25'
            pattern1 = rf"\b{month_name}\s+(\d{{1,2}})(?:st|nd|rd|th)?\b"
            pattern2 = rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?{month_name}\b"
            
            m1 = re.search(pattern1, cleaned)
            m2 = re.search(pattern2, cleaned)
            day_str = m1.group(1) if m1 else (m2.group(1) if m2 else None)
            
            if day_str:
                day_val = int(day_str)
                year_val = clinic_today.year
                try:
                    candidate = date(year_val, month_num, day_val)
                    if candidate < clinic_today:
                        # If date already passed this year, candidate is next year
                        candidate = date(year_val + 1, month_num, day_val)
                    return candidate, None
                except ValueError:
                    return None, f"Invalid day {day_val} for month {month_name.title()}."

        return None, None

    def parse_time(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract and normalize time from user speech to 'HH:MM' 24-hour format.
        Handles '10 AM', '10:30', '2:30 PM', 'at 9', '14:00', 'morning', 'afternoon'.
        
        Returns:
            (normalized_hh_mm, error_message)
        """
        if not text:
            return None, None

        cleaned = text.lower().strip()

        # 1. Explicit 12-hour or 24-hour format with AM/PM (e.g. '10:30 am', '9 am', '2:30 pm', '4 pm')
        time_ampm_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", cleaned)
        if time_ampm_match:
            hours = int(time_ampm_match.group(1))
            minutes = int(time_ampm_match.group(2) or 0)
            meridiem = time_ampm_match.group(3)

            if hours < 1 or hours > 12 or minutes not in (0, 30):
                return None, f"Appointments are scheduled on the hour or half-hour (e.g., 10:00 AM or 10:30 AM)."

            if meridiem == "pm" and hours != 12:
                hours += 12
            elif meridiem == "am" and hours == 12:
                hours = 0

            return f"{hours:02d}:{minutes:02d}", None

        # 2. 24-hour format 'HH:MM' (e.g. '14:30', '10:00', '09:30')
        hhmm_match = re.search(r"\b([01]?\d|2[0-3]):(00|30)\b", cleaned)
        if hhmm_match:
            hours = int(hhmm_match.group(1))
            minutes = int(hhmm_match.group(2))
            return f"{hours:02d}:{minutes:02d}", None

        # 3. Plain number following 'at' (e.g. 'at 10', 'at 9', 'at 2', 'at 11')
        at_match = re.search(r"\bat\s+(\d{1,2})\b", cleaned)
        if at_match:
            val = int(at_match.group(1))
            # Clinic hours are generally 09:00 to 17:00
            if 1 <= val <= 5:
                # 1 to 5 means 13:00 to 17:00 in afternoon
                val += 12
            elif 9 <= val <= 12:
                pass  # Morning 09:00 - 12:00
            else:
                return None, f"Clinic hours are between 9:00 AM and 5:00 PM."
            return f"{val:02d}:00", None

        return None, None

    def format_date_for_speech(self, target_date: date) -> str:
        """
        Format date naturally for spoken audio (e.g. 'Wednesday, November 25th').
        """
        day_num = target_date.day
        if 11 <= day_num <= 13:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day_num % 10, "th")
        return target_date.strftime(f"%A, %B {day_num}{suffix}")

    def format_time_for_speech(self, hh_mm: str) -> str:
        """
        Format 24-hour 'HH:MM' into spoken 12-hour format (e.g. '10:00' -> '10:00 AM', '14:30' -> '2:30 PM').
        """
        try:
            t = time.fromisoformat(hh_mm)
            return t.strftime("%I:%M %p").lstrip("0")
        except Exception:
            return hh_mm


# Global singleton instance
datetime_service = DateTimeService()
