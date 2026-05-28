"""
API key authentication and authorisation for the Partner API.

Looks up API keys from the `api_keys` DynamoDB table, validates site access
via `permitted_site_ids`, and checks optional key expiry via `expires_at`.

Key lookups are cached in-memory for at most 60 seconds to support revocation
within the SLA.
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
    """
    now = time.monotonic()

    # Check cache first
    cached = _cache.get(api_key)
    if cached is not None:
        record, expires_at_mono = cached
        if now < expires_at_mono:
            return record
        del _cache[api_key]

    # Fetch from DynamoDB via GSI on api_key
    try:
        table = _get_dynamodb_table()
        from boto3.dynamodb.conditions import Key
        response = table.query(
            IndexName="api_key-index",
            KeyConditionExpression=Key("api_key").eq(api_key),
            Limit=1,
        )
    except Exception as exc:
        logger.error("DynamoDB lookup failed for api_key: %s", exc)
        raise AuthError("Authentication service unavailable") from exc

    items = response.get("Items", [])
    item = items[0] if items else None

    if item is not None:
        _cache[api_key] = (item, now + _CACHE_TTL_SECONDS)
    return item


def _is_expired(expires_at: Optional[str]) -> bool:
    """
    Return True if the given ISO 8601 expires_at string is in the past.
    """
    if not expires_at:
        return False
    try:
        expiry_dt = datetime.fromisoformat(expires_at)
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
    """
    record = _lookup_key(api_key)

    if record is None:
        raise AuthError("API key not found")

    expires_at = record.get("expires_at")
    if _is_expired(expires_at):
        raise AuthError("API key has expired")

    permitted_site_ids: List[str] = list(record.get("permitted_site_ids") or [])
    if site_id not in permitted_site_ids:
        raise ForbiddenError(
            f"API key does not permit access to site '{site_id}'"
        )

    return permitted_site_ids
