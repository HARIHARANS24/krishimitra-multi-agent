"""Security package: input validation, rate limiting, prompt-injection
guarding, PII redaction, secrets management and secure file handling.
"""
from .input_validation import ValidationError, sanitize_free_text
from .rate_limiter import global_rate_limiter, RateLimitExceeded
from .prompt_injection_guard import guard_or_raise, scan as scan_injection
from .data_filter import redact_pii, redact_for_llm_prompt, redact_dict_for_logging
from .secrets_manager import mask, require, get_gemini_key_safe

__all__ = [
    "ValidationError",
    "sanitize_free_text",
    "global_rate_limiter",
    "RateLimitExceeded",
    "guard_or_raise",
    "scan_injection",
    "redact_pii",
    "redact_for_llm_prompt",
    "redact_dict_for_logging",
    "mask",
    "require",
    "get_gemini_key_safe",
]
