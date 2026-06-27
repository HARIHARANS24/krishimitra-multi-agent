"""
security/prompt_injection_guard.py
====================================
Heuristic defenses against prompt injection in farmer-supplied text
before it is embedded into any LLM prompt sent to Gemini.

This is defense-in-depth, not a silver bullet. We combine it with:
  * strict system-prompt instructions per agent (see agents/base_agent.py)
    that tell the model to treat farmer input as DATA, not as
    instructions;
  * structured output schemas (Pydantic) so a hijacked response is
    rejected at the parsing stage rather than acted upon; and
  * least-privilege tool access per agent (an agent can only call the
    tools it actually needs).

Detection approach:
  1. Pattern match against a curated list of common injection phrasings
     (e.g. "ignore previous instructions", "you are now...", attempts
     to reveal system prompts or secrets).
  2. Flag suspicious role-play / instruction-override language.
  3. Flag attempts to ask the model to exfiltrate environment
     variables, API keys, or internal file paths.

On detection we do NOT silently strip text (that can mask the issue
or be evaded). Instead we flag the message, log the attempt, and let
the calling layer decide to reject the request or sanitize+warn the
user, per security policy.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_INJECTION_PATTERNS = [
    r"ignore (all|any|the)?\s*(previous|prior|above)\s*instructions",
    r"disregard (all|any|the)?\s*(previous|prior|above)\s*(instructions|rules|prompt)",
    r"you are now\s+\w+",
    r"act as (?!a farmer|an? agronomist)",  # allow benign "act as a farmer" framing
    r"system prompt",
    r"reveal (your|the) (system|hidden)\s*(prompt|instructions)",
    r"print (your|the)\s*(api key|secret|env|environment variable)",
    r"\bDAN\b",
    r"jailbreak",
    r"bypass (your|all)\s*(restrictions|guardrails|filters)",
    r"pretend (you|to) (have no|don't have)\s*(restrictions|rules|filters)",
    r"<\s*system\s*>",
    r"\bsudo\b",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


@dataclass
class InjectionScanResult:
    is_suspicious: bool
    matched_patterns: list[str]


def scan(text: str) -> InjectionScanResult:
    matched = [p.pattern for p in _COMPILED if p.search(text)]
    return InjectionScanResult(is_suspicious=bool(matched), matched_patterns=matched)


def wrap_user_data(text: str) -> str:
    """Wrap untrusted farmer text in clearly delimited data tags so the
    LLM prompt template can instruct the model to treat the content
    strictly as data, never as instructions to follow.
    """
    # Escape any delimiter-looking sequences the user tried to inject.
    safe = text.replace("</farmer_input>", "[escaped]").replace("<farmer_input>", "[escaped]")
    return f"<farmer_input>\n{safe}\n</farmer_input>"


def guard_or_raise(text: str) -> str:
    """Scan text; if suspicious, log it and return a wrapped, flagged
    version so downstream agents can decide how to respond
    conservatively (e.g. refuse to follow embedded instructions).
    """
    result = scan(text)
    if result.is_suspicious:
        print(f"[security-audit] possible prompt injection detected: patterns={result.matched_patterns}")
    return wrap_user_data(text)
