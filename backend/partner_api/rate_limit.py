"""
In-memory rolling window rate limiter for the Partner API.
"""
import time
from typing import List

class RateLimitError(Exception):
    """Raised when an API key exceeds the allowed request rate."""

_counters: dict = {}

def check_rate_limit(
    api_key: str,
    max_requests: int = 60,
    window_seconds: int = 60,
) -> None:
    """
    Check and update the rolling window rate limit for the given API key.
    """
    now = time.time()
    cutoff = now - window_seconds

    if api_key not in _counters:
        _counters[api_key] = []

    timestamps: List[float] = _counters[api_key]
    _counters[api_key] = [ts for ts in timestamps if ts > cutoff]
    timestamps = _counters[api_key]

    if len(timestamps) >= max_requests:
        raise RateLimitError(
            f"Rate limit exceeded: maximum {max_requests} requests per "
            f"{window_seconds} seconds allowed per API key"
        )

    timestamps.append(now)
