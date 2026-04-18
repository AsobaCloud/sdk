"""
API key authentication and authorisation for the Inverter Telemetry API.

Looks up API keys from the `api_keys` DynamoDB table, validates site access
via `permitted_site_ids`, and checks optional key expiry via `expires_at`.

Key lookups are cached in-memory for at most 60 seconds to support revocation
within the SLA (Requirements 13.1, 13.2, 13.3).
"""
import logging
import os
import time
from datetime import datetime, timezone
from typing import List, Optional

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AuthError(Exception):
    """Raised when an API key is missing, not found, or has expired."""


class ForbiddenError(Exception):
    """Raised when an API key does not permit access to the requested site."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_TABLE_NAME = os.environ.get("API_KEYS_TABLE", "api_keys")
_AWS_REGION = "af-south-1"
_CACHE_TTL_SECONDS = 60

# ---------------------------------------------------------------------------
# In-memory cache: api_key -> (record_dict, expiry_monotonic_time)
# ---------------------------------------------------------------------------

_cache: dict = {}


def _get_dynamodb_table():
    """Return a boto3 DynamoDB Table resource."""
    dynamodb = boto3.resource("dynamodb", region_name=_AWS_REGION)
    return dynamodb.Table(_TABLE_NAME)


def _lookup_key(api_key: str) -> Optional[dict]:
    """
    Look up an API key record from DynamoDB by the api_key value, using
    the in-memory cache.

    The api_keys table uses api_key_id as the partition key, so we scan
    with a filter expression on the api_key attribute.

    Returns the item dict if found, or None if not found.
    Cache entries expire after _CACHE_TTL_SECONDS seconds.
    """
    now = time.monotonic()

    # Check cache first
    cached = _cache.get(api_key)
    if cached is not None:
        record, expires_at_mono = cached
        if now < expires_at_mono:
            return record
        del _cache[api_key]

    # Fetch from DynamoDB via GSI on api_key (O(1) lookup, not a scan)
    try:
        table = _get_dynamodb_table()
        from boto3.dynamodb.conditions import Key
        response = table.query(
            IndexName="api_key_index",
            KeyConditionExpression=Key("api_key").eq(api_key),
            Limit=1,
        )
    except Exception as exc:
        logger.error("DynamoDB lookup failed for api_key: %s", exc)
        raise AuthError("Authentication service unavailable") from exc

    items = response.get("Items", [])
    item = items[0] if items else None

    # Only cache successful lookups — never cache None (missing keys)
    # so that a bad request doesn't block retries for 60 seconds
    if item is not None:
        _cache[api_key] = (item, now + _CACHE_TTL_SECONDS)
    return item


def _is_expired(expires_at: Optional[str]) -> bool:
    """
    Return True if the given ISO 8601 expires_at string is in the past.
    Returns False if expires_at is None or empty (no expiry set).
    """
    if not expires_at:
        return False
    try:
        expiry_dt = datetime.fromisoformat(expires_at)
        # Ensure timezone-aware comparison
        if expiry_dt.tzinfo is None:
            expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
        return datetime.now(tz=timezone.utc) >= expiry_dt
    except ValueError:
        logger.warning("Invalid expires_at format: %r — treating as expired", expires_at)
        return True


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------


def authenticate(api_key: str, site_id: str) -> List[str]:
    """
    Authenticate an API key and authorise access to the given site_id.

    Steps:
      1. Look up the key in the `api_keys` table (with 60-second cache).
      2. Raise AuthError if the key is not found.
      3. Raise AuthError if the key has expired (expires_at in the past).
      4. Raise ForbiddenError if site_id is not in permitted_site_ids.

    Returns:
        The list of permitted_site_ids for the key on success.

    Raises:
        AuthError: Key not found, expired, or DynamoDB unavailable.
        ForbiddenError: site_id not in permitted_site_ids.
    """
    record = _lookup_key(api_key)

    if record is None:
        raise AuthError("API key not found")

    # Check expiry (Requirement 13.1, 13.2)
    expires_at = record.get("expires_at")
    if _is_expired(expires_at):
        raise AuthError("API key has expired")

    # Check site authorisation (Requirements 8.5, 8.6)
    permitted_site_ids: List[str] = list(record.get("permitted_site_ids") or [])
    if site_id not in permitted_site_ids:
        raise ForbiddenError(
            f"API key does not permit access to site '{site_id}'"
        )

    return permitted_site_ids
