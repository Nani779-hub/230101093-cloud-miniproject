"""Inference parser for command extraction.

Extracts intent and slots (date, time, place) conforming to schema.json:
- intent: one of the 8 canonical intents
- date: exact verbatim shortest phrase from command without prepositions, or null
- time: exact verbatim shortest phrase from command without prepositions, or null
- place: exact verbatim shortest phrase from command without prepositions, or null
"""
import re
from typing import Any, Dict, Optional

VALID_INTENTS = [
    "alarm_set",
    "alarm_query",
    "calendar_set",
    "calendar_query",
    "calendar_remove",
    "weather_query",
    "datetime_query",
    "recommendation_events",
]

# Common date expressions in SLURP
DATE_PATTERNS = [
    r"\b(today|tomorrow|yesterday)\b",
    r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)(?:s)?\b",
    r"\b(?:the\s+)?weekend(?:\s+after\s+next)?\b",
    r"\b(?:the\s+month\s+of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    r"\b(next\s+week|this\s+week|next\s+month)\b",
    r"\b(?:the\s+)?\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\b",
]

# Common time expressions in SLURP
TIME_PATTERNS = [
    r"\b(\d{1,2}(?::\d{2})?\s*(?:am|pm))\b",
    r"\b((?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)(?:\s*(?:am|pm|hundred|o'clock))?)\b",
    r"\b(noon|midnight)\b",
    r"\b(after\s+\w+\s+hours?|in\s+\w+\s+minutes?)\b",
    r"\b(\d+\s+hundred)\b",
]

# Cities and locations in SLURP commands
PLACE_PATTERNS = [
    r"\b(london|paris|new\s+york|tokyo|washington|los\s+angeles|chicago|seattle|san\s+francisco|boston|berlin|beijing|sydney|rome|toronto)\b",
    r"\b(?:at|in|for)\s+([a-z\s]+?)(?:\s+(?:right\s+now|today|tomorrow|weather|time))?\b",
]


def extract_slot(text: str, patterns: list) -> Optional[str]:
    """Extract shortest matching phrase from text without leading prepositions."""
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1) if m.groups() and m.group(1) else m.group(0)
            val = val.strip()
            # Strip leading prepositions if captured
            val = re.sub(r"^(?:at|on|in|for)\s+", "", val, flags=re.IGNORECASE).strip()
            # Verify exact verbatim presence in original text
            if val and val in text:
                return val
    return None


def predict_intent(text: str) -> str:
    """Classify command text into one of the 8 canonical intents."""
    t = text.lower()

    # Alarm intents
    if "alarm" in t or "wake me" in t:
        if any(w in t for w in ["check", "list", "what", "is there", "do i have", "query", "any"]):
            return "alarm_query"
        return "alarm_set"

    # Calendar remove
    if any(w in t for w in ["cancel", "delete", "remove", "clear"]) and any(w in t for w in ["calendar", "meeting", "event", "appointment", "reminder"]):
        return "calendar_remove"

    # Weather
    if any(w in t for w in ["weather", "rain", "snow", "sunny", "forecast", "temperature", "cold", "hot", "outside"]):
        return "weather_query"

    # Datetime query
    if any(w in t for w in ["what time", "current time", "what is the date", "what date", "tell me the time", "time at", "time in", "what day is"]):
        return "datetime_query"

    # Recommendations / events
    if any(w in t for w in ["recommend", "suggest", "events", "concert", "movie", "show", "happening", "things to do"]):
        return "recommendation_events"

    # Calendar query vs set
    if any(w in t for w in ["calendar", "meeting", "schedule", "reminder", "free", "busy", "event", "appointment"]):
        if any(w in t for w in ["do i have", "is there", "what is", "check", "am i", "free for", "list", "show"]):
            return "calendar_query"
        return "calendar_set"

    # Default fallback heuristics
    if "time" in t:
        return "datetime_query"
    return "calendar_query"


class CommandParser:
    """Command parser serving intent and slot predictions."""

    def __init__(self, model_version: str = "v1.0.0"):
        self.model_version = model_version

    def parse(self, text: str) -> Dict[str, Any]:
        """Parse raw text command into the 4-key JSON frame."""
        clean_text = str(text or "").strip()

        intent = predict_intent(clean_text)
        date = extract_slot(clean_text, DATE_PATTERNS)
        time = extract_slot(clean_text, TIME_PATTERNS)
        place = extract_slot(clean_text, PLACE_PATTERNS)

        # Context-dependent slot nullification
        if intent in ("alarm_set", "alarm_query"):
            place = None  # Alarms do not take places

        return {
            "intent": intent,
            "date": date,
            "time": time,
            "place": place,
        }
