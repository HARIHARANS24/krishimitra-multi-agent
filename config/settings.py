"""
config/settings.py
===================
Centralized configuration loader for KrishiMitra AI.

All other modules should import configuration from here instead of
calling os.getenv() directly. This gives us:
  * one place to validate required settings at startup
  * easy mocking in tests
  * a single source of truth for defaults

Security note: this module reads secrets from environment variables
(populated via python-dotenv from a local .env file that is NOT
committed to version control -- see security/secrets_manager.py for
the runtime guard that double-checks this).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load the .env file once, as early as possible.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    try:
        return int(val) if val else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # --- Gemini ---
    google_api_key: str = field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    gemini_model_pro: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL_PRO", "gemini-2.0-pro"))

    # --- Weather ---
    weather_api_key: str = field(default_factory=lambda: os.getenv("WEATHER_API_KEY", ""))
    weather_api_base_url: str = field(
        default_factory=lambda: os.getenv("WEATHER_API_BASE_URL", "https://api.open-meteo.com/v1")
    )

    # --- Market ---
    market_api_key: str = field(default_factory=lambda: os.getenv("MARKET_API_KEY", ""))
    market_api_base_url: str = field(
        default_factory=lambda: os.getenv("MARKET_API_BASE_URL", "https://api.data.gov.in/resource")
    )

    # --- Database ---
    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "./database/krishimitra.db"))

    # --- Security ---
    secret_key: str = field(default_factory=lambda: os.getenv("SECRET_KEY", ""))
    rate_limit_per_minute: int = field(default_factory=lambda: _get_int("RATE_LIMIT_PER_MINUTE", 30))
    max_input_length: int = field(default_factory=lambda: _get_int("MAX_INPUT_LENGTH", 2000))
    enable_prompt_injection_guard: bool = field(
        default_factory=lambda: _get_bool("ENABLE_PROMPT_INJECTION_GUARD", True)
    )
    enable_pii_filter: bool = field(default_factory=lambda: _get_bool("ENABLE_PII_FILTER", True))

    # --- App ---
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development"))
    default_language: str = field(default_factory=lambda: os.getenv("DEFAULT_LANGUAGE", "en"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def has_gemini_key(self) -> bool:
        return bool(self.google_api_key) and self.google_api_key != "your_gemini_api_key_here"

    def validate(self) -> list[str]:
        """Return a list of human-readable warnings about missing config.
        Never raises -- the app should run in a degraded 'demo mode'
        with simulated data if real API keys are absent.
        """
        warnings = []
        if not self.has_gemini_key():
            warnings.append(
                "GOOGLE_API_KEY is not set. Agents will run in offline/simulated reasoning mode."
            )
        if not self.secret_key or self.secret_key == "replace_with_a_long_random_string":
            warnings.append("SECRET_KEY is using a placeholder value. Set a strong secret before production use.")
        return warnings


SUPPORTED_LANGUAGES = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
}

settings = Settings()
