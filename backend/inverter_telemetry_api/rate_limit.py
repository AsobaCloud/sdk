"""
In-memory rolling window rate limiter for the Inverter Telemetry API.

Enforces a maximum number of requests per API key within a sliding time window.
Uses module-level state so the counter persists across Lambda invocations within
the same execution environment (warm container).

Requirements: 11.5, 11.8
"""
import time
from typing import List

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RateLimitError(Exception):
    """Raised when an API key exceeds the allowed request rate."""


# ---------------------------------------------------------------------------
# Module-level rolling window counters
# Maps api_key -> list of request timestamps (float, from time.time())
# ---------------------------------------------------------------------------

_counters: dict = {}


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def check_rate_limit(
    api_key: str,
    max_requests: int = 60,
    window_seconds: int = 60,
) -> None:
    """
    Check and update the rolling window rate limit for the given API key.

    Algorithm:
      1. Prune timestamps older than window_seconds from the key's list.
      2. If the number of remaining timestamps >= max_requests, raise RateLimitError.
      3. Append the current timestamp.

    Args:
        api_key: The API key to rate-limit.
        max_requests: Maximum number of requests allowed within the window.
        window_seconds: Length of the rolling window in seconds.

    Raises:
        RateLimitError: If the rate limit has been exceeded.
    """
    now = time.time()
    cutoff = now - window_seconds

    # Initialise counter list if this is the first request for this key
    if api_key not in _counters:
        _counters[api_key] = []

    timestamps: List[float] = _counters[api_key]

    # Prune expired timestamps (older than the window)
    _counters[api_key] = [ts for ts in timestamps if ts > cutoff]
    timestamps = _counters[api_key]

    if len(timestamps) >= max_requests:
        raise RateLimitError(
            f"Rate limit exceeded: maximum {max_requests} requests per "
            f"{window_seconds} seconds allowed per API key"
        )

    timestamps.append(now)
