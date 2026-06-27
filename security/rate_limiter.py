"""
security/rate_limiter.py
=========================
A lightweight, dependency-free sliding-window rate limiter.

Why a custom in-memory limiter (instead of e.g. Redis) for this
capstone: KrishiMitra is designed to also run as a single-process
Streamlit app / small Cloud Run instance, so we avoid requiring an
external service just to enforce basic abuse protection. The
interface is intentionally small so it can be swapped for a
Redis-backed implementation in a multi-instance production deployment
without touching calling code (see docs/deployment_guide.md).

Strategy: sliding window counter per identity key (user id, session
id, or IP address), configurable requests-per-minute.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from config.settings import settings


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: float):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry after {retry_after_seconds:.1f}s.")


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: float = 0.0


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int | None = None, window_seconds: float = 60.0):
        self.max_requests = max_requests or settings.rate_limit_per_minute
        self.window_seconds = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, identity: str) -> RateLimitResult:
        """Check & record a request. Thread-safe."""
        now = time.monotonic()
        with self._lock:
            window = self._hits[identity]
            # Drop timestamps outside the window.
            cutoff = now - self.window_seconds
            while window and window[0] < cutoff:
                window.popleft()

            if len(window) >= self.max_requests:
                retry_after = self.window_seconds - (now - window[0])
                return RateLimitResult(allowed=False, remaining=0, retry_after_seconds=max(retry_after, 0.1))

            window.append(now)
            remaining = self.max_requests - len(window)
            return RateLimitResult(allowed=True, remaining=remaining)

    def enforce(self, identity: str) -> None:
        """Raise RateLimitExceeded if the caller is over budget."""
        result = self.check(identity)
        if not result.allowed:
            raise RateLimitExceeded(result.retry_after_seconds)


# A process-wide limiter shared by the Streamlit app / agents.
global_rate_limiter = SlidingWindowRateLimiter()
