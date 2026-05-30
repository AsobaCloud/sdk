"""
Lambda handler for the Partner API.

Serves pre-computed JSON snapshots from S3 with ETag support for conditional GETs.
"""
import json
import logging
import os
import boto3
from botocore.exceptions import ClientError

from .auth import AuthError, ForbiddenError, authenticate
from .validators import ValidationError, validate_partner_params
from .rate_limit import RateLimitError, check_rate_limit

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

S3_BUCKET = os.environ.get("PARTNER_SNAPSHOTS_BUCKET", "partner-snapshots")
s3 = boto3.client("s3")

_ERROR_MESSAGES = {
    400: "Invalid request",
    401: "Unauthorized",
    403: "Access denied",
    404: "Not found",
    429: "Too many requests",
}
_5XX_MESSAGE = "Service unavailable"

def _response(status_code: int, body: dict, headers: dict = None) -> dict:
    resp = {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
    if headers:
        resp["headers"].update(headers)
    return resp

def _error(status_code: int) -> dict:
    message = _ERROR_MESSAGES.get(status_code, _5XX_MESSAGE)
    return _response(status_code, {"error": message})

def _get_snapshot(kind: str, site_id: str, if_none_match: str = None):
    key = f"{kind}/{site_id}.json"
    try:
        params = {"Bucket": S3_BUCKET, "Key": key}
        if if_none_match:
            params["IfNoneMatch"] = if_none_match
            
        resp = s3.get_object(**params)
        body = resp["Body"].read().decode("utf-8")
        etag = resp.get("ETag")
        return _response(200, json.loads(body), {"ETag": etag})
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "304" or error_code == "NotModified":
            return _response(304, {})
        if error_code == "NoSuchKey":
            return _error(404)
        logger.exception("S3 error for key %s", key)
        return _error(500)

def lambda_handler(event: dict, context) -> dict:
    """Main Lambda entry point."""
    path = event.get("path") or event.get("rawPath", "")
    _ = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")
    params = event.get("queryStringParameters") or {}
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    api_key = headers.get("x-api-key", "")
    if_none_match = headers.get("if-none-match")

    if not api_key:
        return _error(401)
    
    try:
        validated = validate_partner_params(params, path)
        site_id = validated["site_id"]
        
        # Authenticate and check rate limit
        authenticate(api_key, site_id)
        check_rate_limit(api_key)
        
        # Route based on path
        kind = None
        if path == "/kpi-rollup":
            kind = "kpi-rollup"
        elif path == "/maintenance-signals":
            kind = "maintenance-signals"
        elif path == "/forecast-snapshot":
            kind = "forecast-snapshot"
        elif path == "/snapshot":
            kind = validated["kind"]
        
        if not kind:
            return _error(400)
        
        return _get_snapshot(kind, site_id, if_none_match)
        
    except ValidationError:
        return _error(400)
    except AuthError:
        return _error(401)
    except ForbiddenError:
        return _error(403)
    except RateLimitError:
        return _error(429)
    except Exception:
        logger.exception("Unhandled error in lambda_handler")
        return _error(500)
