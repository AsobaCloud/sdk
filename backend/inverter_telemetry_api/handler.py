"""
Lambda handler entry point for the Inverter Telemetry API.

Routes:
  GET /telemetry/inverter  — query single inverter telemetry
  GET /telemetry/site      — query all inverters at a site

Error responses use generic messages only (Requirements 14.2, 14.3).
"""
import json
import logging

from .auth import AuthError, ForbiddenError, authenticate
from .validators import ValidationError, validate_inverter_params, validate_site_params, validate_data_period_params
from .db import query_inverter_telemetry, query_site_telemetry, get_data_period
from .rate_limit import RateLimitError, check_rate_limit

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Generic error messages — no internal details exposed (Req 14.2, 14.3)
# ---------------------------------------------------------------------------
_ERROR_MESSAGES = {
    400: "Invalid request",
    401: "Unauthorized",
    403: "Access denied",
    429: "Too many requests",
}
_5XX_MESSAGE = "Service unavailable"


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def _error(status_code: int) -> dict:
    message = _ERROR_MESSAGES.get(status_code, _5XX_MESSAGE)
    return _response(status_code, {"error": message})


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------

def _handle_inverter(params: dict, api_key: str) -> dict:
    """Handle GET /telemetry/inverter."""
    try:
        validated = validate_inverter_params(params)
    except ValidationError:
        return _error(400)

    site_id = validated["site_id"]

    try:
        authenticate(api_key, site_id)
    except AuthError:
        return _error(401)
    except ForbiddenError:
        return _error(403)

    try:
        check_rate_limit(api_key)
    except RateLimitError:
        return _error(429)

    try:
        records = query_inverter_telemetry(
            asset_id=validated["asset_id"],
            site_id=site_id,
            start=validated["start"],
            end=validated["end"],
            resolution=validated.get("resolution", "5min"),
            limit=validated.get("limit", 100),
            cursor=validated.get("cursor"),
        )
    except Exception:
        logger.exception("Error querying inverter telemetry")
        return _error(500)

    return _response(200, {"records": records})


def _handle_site(params: dict, api_key: str) -> dict:
    """Handle GET /telemetry/site."""
    try:
        validated = validate_site_params(params)
    except ValidationError:
        return _error(400)

    site_id = validated["site_id"]

    try:
        authenticate(api_key, site_id)
    except AuthError:
        return _error(401)
    except ForbiddenError:
        return _error(403)

    try:
        check_rate_limit(api_key)
    except RateLimitError:
        return _error(429)

    try:
        records = query_site_telemetry(
            site_id=site_id,
            start=validated["start"],
            end=validated["end"],
            resolution=validated.get("resolution", "5min"),
            limit=validated.get("limit", 100),
        )
    except Exception:
        logger.exception("Error querying site telemetry")
        return _error(500)

    return _response(200, {"records": records})


def _handle_data_period(params: dict, api_key: str) -> dict:
    """Handle GET /telemetry/data-period."""
    try:
        validated = validate_data_period_params(params)
    except ValidationError:
        return _error(400)

    site_id = validated["site_id"]

    try:
        authenticate(api_key, site_id)
    except AuthError:
        return _error(401)
    except ForbiddenError:
        return _error(403)

    try:
        check_rate_limit(api_key)
    except RateLimitError:
        return _error(429)

    try:
        result = get_data_period(
            site_id=site_id,
            asset_id=validated.get("asset_id"),
        )
    except Exception:
        logger.exception("Error getting data period")
        return _error(500)

    return _response(200, result)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def lambda_handler(event: dict, context) -> dict:
    """Main Lambda entry point — routes requests to the appropriate handler."""
    path = event.get("path") or event.get("rawPath", "")
    method = event.get("httpMethod") or event.get("requestContext", {}).get(
        "http", {}
    ).get("method", "")

    params = event.get("queryStringParameters") or {}
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    api_key = headers.get("x-api-key", "")

    if not api_key:
        return _error(401)

    try:
        if method == "GET" and path == "/telemetry/inverter":
            return _handle_inverter(params, api_key)

        if method == "GET" and path == "/telemetry/site":
            return _handle_site(params, api_key)

        if method == "GET" and path == "/telemetry/data-period":
            return _handle_data_period(params, api_key)

        # Unknown route
        return _error(400)

    except Exception:
        logger.exception("Unhandled error in lambda_handler")
        return _error(500)
