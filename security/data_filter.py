"""
security/data_filter.py
=========================
Filters sensitive data (PII) both on the way IN (farmer profile data
stored in SQLite) and on the way OUT (anything logged or sent to a
third-party LLM/API).

Farmer profiles may contain: phone numbers, Aadhaar-like ID numbers,
bank account numbers (for scheme eligibility flows), and precise GPS
coordinates of farmland. None of this should ever be sent to the
Gemini API as part of a prompt, nor written to plaintext logs.
"""

from __future__ import annotations

import re

_PHONE_RE = re.compile(r"\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b")
_AADHAAR_RE = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_BANK_ACCOUNT_RE = re.compile(r"\b\d{9,18}\b")
_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_LATLON_RE = re.compile(r"-?\d{1,3}\.\d{4,},\s*-?\d{1,3}\.\d{4,}")

_PATTERNS = {
    "phone": _PHONE_RE,
    "aadhaar_like": _AADHAAR_RE,
    "email": _EMAIL_RE,
    "gps_coordinates": _LATLON_RE,
}


def redact_pii(text: str) -> str:
    """Replace detected PII with a typed placeholder, e.g. [REDACTED_PHONE]."""
    if not text:
        return text
    redacted = text
    for label, pattern in _PATTERNS.items():
        redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
    return redacted


def redact_for_llm_prompt(text: str) -> str:
    """Stricter redaction applied specifically before text is embedded
    into a prompt sent to an external LLM provider (Gemini). Bank
    account-like long digit sequences are also stripped here, since
    they are too easily confused with legitimate agronomic numbers
    (e.g. land survey numbers) to redact everywhere by default.
    """
    text = redact_pii(text)
    text = _BANK_ACCOUNT_RE.sub("[REDACTED_NUMBER]", text)
    return text


def redact_dict_for_logging(data: dict, sensitive_keys: set[str] | None = None) -> dict:
    """Return a shallow copy of `data` with sensitive keys masked --
    used before writing structured log entries.
    """
    sensitive_keys = sensitive_keys or {
        "phone",
        "phone_number",
        "aadhaar",
        "bank_account",
        "email",
        "password",
        "api_key",
        "gps",
        "latitude",
        "longitude",
    }
    out = {}
    for k, v in data.items():
        if k.lower() in sensitive_keys:
            out[k] = "[REDACTED]"
        elif isinstance(v, str):
            out[k] = redact_pii(v)
        else:
            out[k] = v
    return out
