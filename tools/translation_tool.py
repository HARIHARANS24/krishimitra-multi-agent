"""
tools/translation_tool.py
============================
Regional language support architecture.

Approach: rather than translating every dynamically-generated sentence
through the LLM (slow, costly, and harder to test deterministically),
KrishiMitra uses a hybrid strategy:

  1. UI strings (labels, buttons, page titles) are translated via
     static JSON dictionaries in frontend/i18n/{lang}.json -- instant,
     free, and consistent.
  2. Dynamic agent-generated content (the actual recommendation text)
     is translated on demand via the Gemini API when a non-English
     language is selected, with a local fallback (basic phrase
     substitution) if no API key is configured -- so the app still
     "supports" Tamil/Hindi end-to-end in demo/offline mode, just with
     lower-fidelity translation of free-form text.

This module implements step 2 plus the loader for step 1.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from config.settings import settings
from security.secrets_manager import get_gemini_key_safe

I18N_DIR = Path(__file__).resolve().parent.parent / "frontend" / "i18n"

# Minimal offline fallback phrase table for common recommendation
# vocabulary, used only when no Gemini key is configured.
_OFFLINE_PHRASES = {
    "ta": {
        "Recommended Crop": "பரிந்துரைக்கப்பட்ட பயிர்",
        "Confidence": "நம்பகத்தன்மை",
        "Alternative Crops": "மாற்று பயிர்கள்",
        "Reason": "காரணம்",
        "Weather": "வானிலை",
        "Fertilizer": "உரம்",
        "Irrigation": "நீர்ப்பாசனம்",
    },
    "hi": {
        "Recommended Crop": "अनुशंसित फसल",
        "Confidence": "विश्वास स्तर",
        "Alternative Crops": "वैकल्पिक फसलें",
        "Reason": "कारण",
        "Weather": "मौसम",
        "Fertilizer": "खाद",
        "Irrigation": "सिंचाई",
    },
}


@lru_cache(maxsize=8)
def load_ui_strings(lang_code: str) -> dict:
    path = I18N_DIR / f"{lang_code}.json"
    if not path.exists():
        path = I18N_DIR / "en.json"
    return json.loads(path.read_text(encoding="utf-8"))


def translate_dynamic_text(text: str, target_lang: str) -> str:
    """Translate agent-generated free text into the target language.
    Falls back gracefully when no Gemini key is configured -- applies
    simple phrase substitution and otherwise returns the original
    English text with a note, rather than failing.
    """
    if target_lang == "en" or not text:
        return text

    api_key = get_gemini_key_safe()
    if api_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(settings.gemini_model)
            lang_name = {"ta": "Tamil", "hi": "Hindi"}.get(target_lang, target_lang)
            prompt = (
                f"Translate the following agricultural advisory text into {lang_name}. "
                "Keep numbers, crop names, and units accurate. Return ONLY the translation, "
                f"no preamble.\n\nText:\n{text}"
            )
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:  # pragma: no cover - network/SDK errors
            print(f"[translation_tool] Gemini translation failed, using offline fallback: {exc}")

    # Offline fallback: substitute known phrases, leave the rest as-is.
    phrases = _OFFLINE_PHRASES.get(target_lang, {})
    translated = text
    for en_phrase, local_phrase in phrases.items():
        translated = translated.replace(en_phrase, local_phrase)
    return translated
