"""Utility functions for parsing and formatting timer durations."""

import re

_DURATION_PATTERN = re.compile(
    r"(\d+)\s*"
    r"(seconds|second|secs|sec|"
    r"minutes|minute|mins|min|"
    r"hours|hour|hrs|hr|"
    r"days|day|"
    r"s|m|h|d)\b",
    re.IGNORECASE,
)

_UNIT_SECONDS = {
    "d": 86_400,
    "day": 86_400,
    "days": 86_400,
    "h": 3_600,
    "hr": 3_600,
    "hrs": 3_600,
    "hour": 3_600,
    "hours": 3_600,
    "m": 60,
    "min": 60,
    "mins": 60,
    "minute": 60,
    "minutes": 60,
    "s": 1,
    "sec": 1,
    "secs": 1,
    "second": 1,
    "seconds": 1,
}


def parse_duration(value: str) -> int:
    """Convert a human-readable duration into total seconds.

    Examples:
        30s
        5m
        1h 30m
        3 days 12 hours
    """

    if not value or not value.strip():
        raise ValueError("Duration cannot be empty.")

    cleaned_value = value.strip().lower()
    matches = list(_DURATION_PATTERN.finditer(cleaned_value))

    if not matches:
        raise ValueError(
            "Invalid duration. Try formats such as '30s', '5m', or '1h 30m'."
        )

    unmatched_text = _DURATION_PATTERN.sub("", cleaned_value)
    unmatched_text = re.sub(r"[\s,]+", "", unmatched_text)

    if unmatched_text:
        raise ValueError(f"Invalid duration content: {unmatched_text!r}")

    total_seconds = 0

    for match in matches:
        amount = int(match.group(1))
        unit = match.group(2).lower()
        total_seconds += amount * _UNIT_SECONDS[unit]

    if total_seconds <= 0:
        raise ValueError("Duration must be greater than zero.")

    return total_seconds


def format_duration(total_seconds: int) -> str:
    """Format seconds as a compact human-readable duration."""

    if total_seconds < 0:
        raise ValueError("Duration cannot be negative.")

    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []

    if days:
        parts.append(f"{days}d")

    if hours:
        parts.append(f"{hours}h")

    if minutes:
        parts.append(f"{minutes}m")

    if seconds or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def format_countdown(total_seconds: int) -> str:
    """Format seconds as DD:HH:MM:SS or HH:MM:SS."""

    if total_seconds < 0:
        total_seconds = 0

    days, remainder = divmod(total_seconds, 86_400)
    hours, remainder = divmod(remainder, 3_600)
    minutes, seconds = divmod(remainder, 60)

    if days:
        return f"{days:02}:{hours:02}:{minutes:02}:{seconds:02}"

    return f"{hours:02}:{minutes:02}:{seconds:02}"

