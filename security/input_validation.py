"""
security/input_validation.py
=============================
Validates and sanitizes all farmer-supplied input before it reaches
any agent, tool, MCP server, or database query.

Why this matters for KrishiMitra:
  * Farmers interact via free-text chat (Advisory Assistant) and
    structured forms (Crop Planner, Settings). Both surfaces are
    untrusted input.
  * Inputs are later interpolated into LLM prompts (risk: prompt
    injection) and, in the database layer, into SQL (risk: injection)
    even though we use parameterized queries as defense-in-depth.

This module performs:
  * length limits
  * character allow-listing for structured fields (region names, crop
    names, numeric ranges)
  * type/range coercion for numeric agronomic inputs (rainfall, area)
  * rejection of control characters / null bytes
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from config.settings import settings

# Allow letters (incl. basic unicode for Tamil/Hindi), numbers, spaces and
# a small set of punctuation commonly found in place names / queries.
_SAFE_TEXT_RE = re.compile(r"^[\w\s.,!?'/()\-:;%₹\u0B80-\u0BFF\u0900-\u097F]*$", re.UNICODE)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

VALID_SOIL_TYPES = {"alluvial", "black", "red", "laterite", "sandy", "clay", "loamy", "saline"}
VALID_SEASONS = {"kharif", "rabi", "zaid", "summer"}


class ValidationError(ValueError):
    pass


@dataclass
class ValidatedQuery:
    text: str
    truncated: bool = False


def sanitize_free_text(raw: str, max_length: int | None = None) -> ValidatedQuery:
    """Sanitize free-text chat input from the Advisory Assistant."""
    if raw is None:
        raise ValidationError("Input cannot be empty.")

    max_len = max_length or settings.max_input_length
    text = raw.strip()

    if not text:
        raise ValidationError("Input cannot be empty.")

    # Strip control / null characters outright -- never allowed.
    text = _CONTROL_CHAR_RE.sub("", text)

    truncated = False
    if len(text) > max_len:
        text = text[:max_len]
        truncated = True

    return ValidatedQuery(text=text, truncated=truncated)


def validate_region_name(region: str) -> str:
    region = (region or "").strip()
    if not region:
        raise ValidationError("Region name is required.")
    if len(region) > 100:
        raise ValidationError("Region name is too long.")
    if not _SAFE_TEXT_RE.match(region):
        raise ValidationError("Region name contains unsupported characters.")
    return region


def validate_soil_type(soil_type: str) -> str:
    st = (soil_type or "").strip().lower()
    if st not in VALID_SOIL_TYPES:
        raise ValidationError(
            f"Unsupported soil type '{soil_type}'. Valid options: {sorted(VALID_SOIL_TYPES)}"
        )
    return st


def validate_season(season: str) -> str:
    s = (season or "").strip().lower()
    if s not in VALID_SEASONS:
        raise ValidationError(f"Unsupported season '{season}'. Valid options: {sorted(VALID_SEASONS)}")
    return s


def validate_numeric_range(value: float, field_name: str, min_v: float, max_v: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{field_name}' must be a number.")
    if not (min_v <= value <= max_v):
        raise ValidationError(f"'{field_name}' must be between {min_v} and {max_v}.")
    return value


def validate_land_area_acres(area: float) -> float:
    return validate_numeric_range(area, "land_area_acres", 0.1, 10000)


def validate_rainfall_mm(rainfall: float) -> float:
    return validate_numeric_range(rainfall, "rainfall_mm", 0, 5000)


def validate_language_code(lang: str) -> str:
    from config.settings import SUPPORTED_LANGUAGES

    lang = (lang or "en").strip().lower()
    if lang not in SUPPORTED_LANGUAGES:
        raise ValidationError(f"Unsupported language '{lang}'.")
    return lang
