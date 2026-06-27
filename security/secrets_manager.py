"""
security/secrets_manager.py
============================
Centralizes how secrets (API keys, tokens) are loaded and exposed.

Design decisions:
1. Secrets are ONLY read from environment variables (populated from a
   local, git-ignored .env file). They are never hard-coded, logged,
   or echoed back to the user/UI.
2. `mask()` is used anywhere a secret might end up in a log line or
   error message, so that full keys never appear in plaintext output.
3. `require()` fails loudly (raises) for code paths that truly cannot
   function without a key (e.g. a real Gemini call), while the rest of
   the app is designed to degrade gracefully into simulated/demo mode
   instead of crashing -- appropriate for a farmer-facing tool that
   must stay usable even if a vendor key is missing or rate-limited.
"""

from __future__ import annotations

from config.settings import settings


class MissingSecretError(RuntimeError):
    pass


def mask(secret: str, visible: int = 4) -> str:
    """Mask a secret for safe display in logs/UI, e.g. 'sk-ab12...wxyz'."""
    if not secret:
        return "<empty>"
    if len(secret) <= visible * 2:
        return "*" * len(secret)
    return f"{secret[:visible]}{'*' * 6}{secret[-visible:]}"


def require(value: str, name: str) -> str:
    """Raise MissingSecretError if a required secret is absent/placeholder."""
    placeholder_markers = ("your_", "replace_with", "")
    if not value or any(value.startswith(p) for p in placeholder_markers if p):
        raise MissingSecretError(
            f"Required secret '{name}' is not configured. "
            f"Set it in your .env file before enabling this feature."
        )
    return value


def get_gemini_key_safe() -> str | None:
    """Return the Gemini key if usable, else None (never raises)."""
    if settings.has_gemini_key():
        return settings.google_api_key
    return None


def audit_secret_usage(name: str) -> None:
    """Log (without revealing the value) that a secret was accessed.
    In a production deployment this would write to a structured audit
    log / SIEM rather than stdout.
    """
    print(f"[security-audit] secret accessed: name={name}")
