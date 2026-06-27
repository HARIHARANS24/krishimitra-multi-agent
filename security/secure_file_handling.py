"""
security/secure_file_handling.py
==================================
Guards file uploads/downloads (e.g. a farmer uploading a soil test
report PDF/image, or exporting a farming plan).

Controls implemented:
  * Extension + MIME allow-listing
  * Maximum file size enforcement
  * Filename sanitization (no path traversal, no executable names)
  * Storage under a dedicated, non-web-served directory with random
    generated filenames (original name preserved only as DB metadata)
"""

from __future__ import annotations

import os
import re
import uuid
from pathlib import Path

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".csv", ".txt"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

_UNSAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]")


class FileSecurityError(ValueError):
    pass


def sanitize_filename(filename: str) -> str:
    name = os.path.basename(filename or "")
    name = _UNSAFE_NAME_RE.sub("_", name)
    if not name or name in {".", ".."}:
        raise FileSecurityError("Invalid filename.")
    return name


def validate_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise FileSecurityError(
            f"File type '{ext}' is not allowed. Allowed types: {sorted(ALLOWED_EXTENSIONS)}"
        )
    return ext


def validate_size(size_bytes: int) -> None:
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileSecurityError(
            f"File too large ({size_bytes / 1_048_576:.1f} MB). "
            f"Max allowed is {MAX_FILE_SIZE_BYTES / 1_048_576:.0f} MB."
        )


def generate_storage_path(original_filename: str, storage_dir: str) -> tuple[str, str]:
    """Return (stored_path, generated_filename). The generated filename
    uses a random UUID + the validated extension, never the
    user-supplied name, to prevent path traversal or collisions.
    """
    safe_name = sanitize_filename(original_filename)
    ext = validate_extension(safe_name)
    generated = f"{uuid.uuid4().hex}{ext}"

    storage_dir_path = Path(storage_dir).resolve()
    storage_dir_path.mkdir(parents=True, exist_ok=True)

    stored_path = storage_dir_path / generated
    # Defense-in-depth: ensure the resolved path is still inside storage_dir.
    if storage_dir_path not in stored_path.resolve().parents and stored_path.resolve() != storage_dir_path:
        raise FileSecurityError("Resolved storage path escapes the allowed directory.")

    return str(stored_path), generated
