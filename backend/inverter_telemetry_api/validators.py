"""
Input validation for the Inverter Telemetry API.

Validates query parameters for both /telemetry/inverter and /telemetry/site
endpoints, enforcing pattern constraints, time range limits, and cursor integrity.

Requirements: 11.6, 11.7, 14.1, 14.4
"""
import base64
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ValidationError(Exception):
    """Raised when input parameters fail validation."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAFE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
_MAX_LIMIT = 1000
_DEFAULT_LIMIT = 100
_DEFAULT_RESOLUTION = "5min"
_VALID_RESOLUTIONS = {"5min", "daily"}
_MAX_DAYS = 31


# ---------------------------------------------------------------------------
# Cursor helpers
# ---------------------------------------------------------------------------

def _decode_cursor(cursor: str) -> dict:
    """
    Decode a base64url-encoded JSON cursor string.

    Returns the decoded dict, or raises ValidationError if malformed.
    """
    try:
        # Add padding if needed
        padded = cursor + "=" * (4 - len(cursor) % 4) if len(cursor) % 4 else cursor
        decoded_bytes = base64.urlsafe_b64decode(padded)
        data = json.loads(decoded_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValidationError(f"Cursor is malformed: {exc}") from exc

    if not isinstance(data, dict):
        raise ValidationError("Cursor must decode to a JSON object")

    if "asset_id" not in data:
        raise ValidationError("Cursor is missing required field 'asset_id'")

    if "timestamp" not in data:
        raise ValidationError("Cursor is missing required field 'timestamp'")

    return data


# ---------------------------------------------------------------------------
# Shared validation helpers
# ---------------------------------------------------------------------------

def _validate_safe_id(value: str, field_name: str) -> None:
    """Validate that a string matches SAFE_ID_PATTERN."""
    if not SAFE_ID_PATTERN.match(value):
        raise ValidationError(
            f"'{field_name}' contains invalid characters. "
            f"Only alphanumeric characters, hyphens, and underscores are allowed."
        )


def _validate_time_range(start: str, end: str) -> None:
    """Validate start <= end and span <= 31 days."""
    if start > end:
        raise ValidationError(
            f"'start' must be less than or equal to 'end' (got start={start!r}, end={end!r})"
        )
    # Validate span <= 31 days
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        span = end_dt - start_dt
        if span > timedelta(days=_MAX_DAYS):
            raise ValidationError(
                f"Time range exceeds the maximum allowed span of {_MAX_DAYS} days "
                f"(got {span.days} days)"
            )
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Invalid time range: {exc}") from exc


def _validate_limit(limit_raw: Optional[str]) -> int:
    """Parse and validate the limit parameter."""
    if limit_raw is None:
        return _DEFAULT_LIMIT
    try:
        limit = int(limit_raw)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"'limit' must be an integer (got {limit_raw!r})") from exc
    if limit > _MAX_LIMIT:
        raise ValidationError(
            f"'limit' must not exceed {_MAX_LIMIT} (got {limit})"
        )
    if limit < 1:
        raise ValidationError(f"'limit' must be at least 1 (got {limit})")
    return limit


def _validate_resolution(resolution_raw: Optional[str]) -> str:
    """Parse and validate the resolution parameter."""
    if resolution_raw is None:
        return _DEFAULT_RESOLUTION
    if resolution_raw not in _VALID_RESOLUTIONS:
        raise ValidationError(
            f"'resolution' must be one of {sorted(_VALID_RESOLUTIONS)} (got {resolution_raw!r})"
        )
    return resolution_raw


# ---------------------------------------------------------------------------
# Public validators
# ---------------------------------------------------------------------------

def validate_inverter_params(params: dict) -> dict:
    """
    Validate and normalise query parameters for GET /telemetry/inverter.

    Required: asset_id, site_id, start, end
    Optional: resolution (default "5min"), limit (default 100, max 1000), cursor

    Returns a normalised dict with all validated values.
    Raises ValidationError with a descriptive message on any failure.
    """
    # --- Required fields ---
    for field in ("asset_id", "site_id", "start", "end"):
        if not params.get(field):
            raise ValidationError(f"Missing required parameter: '{field}'")

    asset_id = params["asset_id"]
    site_id = params["site_id"]
    start = params["start"]
    end = params["end"]

    # --- Pattern validation ---
    _validate_safe_id(asset_id, "asset_id")
    _validate_safe_id(site_id, "site_id")

    # --- Time range validation ---
    _validate_time_range(start, end)

    # --- Optional fields ---
    resolution = _validate_resolution(params.get("resolution"))
    limit = _validate_limit(params.get("limit"))

    result = {
        "asset_id": asset_id,
        "site_id": site_id,
        "start": start,
        "end": end,
        "resolution": resolution,
        "limit": limit,
    }

    # --- Cursor validation ---
    cursor = params.get("cursor")
    if cursor:
        cursor_data = _decode_cursor(cursor)
        if cursor_data["asset_id"] != asset_id:
            raise ValidationError(
                f"Cursor 'asset_id' ({cursor_data['asset_id']!r}) does not match "
                f"request 'asset_id' ({asset_id!r})"
            )
        result["cursor"] = cursor

    return result


def validate_site_params(params: dict) -> dict:
    """
    Validate and normalise query parameters for GET /telemetry/site.

    Required: site_id, start, end
    Optional: resolution (default "5min"), limit (default 100, max 1000)

    Returns a normalised dict with all validated values.
    Raises ValidationError with a descriptive message on any failure.
    """
    # --- Required fields ---
    for field in ("site_id", "start", "end"):
        if not params.get(field):
            raise ValidationError(f"Missing required parameter: '{field}'")

    site_id = params["site_id"]
    start = params["start"]
    end = params["end"]

    # --- Pattern validation ---
    _validate_safe_id(site_id, "site_id")

    # --- Time range validation ---
    _validate_time_range(start, end)

    # --- Optional fields ---
    resolution = _validate_resolution(params.get("resolution"))
    limit = _validate_limit(params.get("limit"))

    return {
        "site_id": site_id,
        "start": start,
        "end": end,
        "resolution": resolution,
        "limit": limit,
    }


def validate_data_period_params(params: dict) -> dict:
    """Validate params for GET /telemetry/data-period."""
    if not params.get("site_id"):
        raise ValidationError("Missing required parameter: 'site_id'")
    site_id = params["site_id"]
    _validate_safe_id(site_id, "site_id")
    result = {"site_id": site_id}
    asset_id = params.get("asset_id")
    if asset_id:
        _validate_safe_id(asset_id, "asset_id")
        result["asset_id"] = asset_id
    return result
