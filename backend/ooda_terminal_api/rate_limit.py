"""
Rate limiting for the OODA Terminal API.

Simple in-memory rate limiting based on API key. This is a basic implementation
that tracks request counts per API key with a sliding window approach.

Requirements: 12.5, 12.6, 12.7
"""
import time
from collections import defaultdict, deque
from typing import Dict, Deque

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class RateLimitError(Exception):
    """Raised when an API key exceeds the rate limit."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_RATE_LIMIT_PER_MINUTE = 60
_WINDOW_SIZE_SECONDS = 60

# ---------------------------------------------------------------------------
# In-memory storage: api_key -> deque of request timestamps
# ---------------------------------------------------------------------------

_request_times: Dict[str, Deque[float]] = defaultdict(deque)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def check_rate_limit(api_key: str) -> None:
    """
    Check if the API key has exceeded the rate limit.
    
    Uses a sliding window approach: tracks timestamps of requests in the last
    60 seconds and raises RateLimitError if more than 60 requests.
    
    Raises:
        RateLimitError: If the API key has exceeded 60 requests per minute.
    """
    now = time.time()
    window_start = now - _WINDOW_SIZE_SECONDS
    
    # Get the deque for this API key
    times = _request_times[api_key]
    
    # Remove old timestamps outside the window
    while times and times[0] < window_start:
        times.popleft()
    
    # Check if we're at the limit
    if len(times) >= _RATE_LIMIT_PER_MINUTE:
        raise RateLimitError(f"Rate limit exceeded for API key")
    
    # Add current request timestamp
    times.append(now)