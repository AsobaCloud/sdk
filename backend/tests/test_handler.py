"""
End-to-end behaviour tests for the Lambda handler and supporting modules.

Tests exercise REAL logic with real inputs — no mocks, no patches.

Coverage:
- lambda_handler routing: missing x-api-key → 401
- lambda_handler routing: unknown path → 400
- Error response body format: {"error": "..."}
- validate_inverter_params: invalid asset_id characters → ValidationError
- validate_inverter_params: inverted time range → ValidationError
- validate_inverter_params: time range > 31 days → ValidationError
- validate_inverter_params: limit > 1000 → ValidationError
- validate_site_params: missing required field → ValidationError
- check_rate_limit: 60 calls succeed, 61st raises RateLimitError
- check_rate_limit: counter resets after window expires
- CursorSerializer round-trip via validators._decode_cursor
"""
import base64
import json
import time

import pytest

from backend.inverter_telemetry_api.handler import lambda_handler
from backend.inverter_telemetry_api.validators import (
    ValidationError,
    validate_inverter_params,
    validate_site_params,
    _decode_cursor,
)
from backend.inverter_telemetry_api.rate_limit import (
    RateLimitError,
    check_rate_limit,
    _counters,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(method="GET", path="/telemetry/inverter", params=None, headers=None):
    """Build a minimal API Gateway proxy event dict."""
    return {
        "httpMethod": method,
        "path": path,
        "queryStringParameters": params or {},
        "headers": headers or {},
    }


def _parse_body(response: dict) -> dict:
    return json.loads(response["body"])


# ---------------------------------------------------------------------------
# lambda_handler routing tests
# ---------------------------------------------------------------------------

class TestHandlerRouting:
    def test_missing_api_key_inverter_returns_401(self):
        event = _make_event(
            path="/telemetry/inverter",
            headers={},  # no x-api-key
        )
        response = lambda_handler(event, None)
        assert response["statusCode"] == 401
        body = _parse_body(response)
        assert "error" in body

    def test_missing_api_key_site_returns_401(self):
        event = _make_event(
            path="/telemetry/site",
            headers={},
        )
        response = lambda_handler(event, None)
        assert response["statusCode"] == 401
        body = _parse_body(response)
        assert "error" in body

    def test_unknown_path_returns_400(self):
        event = _make_event(
            path="/unknown/path",
            headers={"x-api-key": "some-key"},
        )
        response = lambda_handler(event, None)
        assert response["statusCode"] == 400
        body = _parse_body(response)
        assert "error" in body

    def test_error_body_contains_generic_message_not_internal_details(self):
        """Error responses must use generic messages — no AWS names, table names, etc."""
        event = _make_event(
            path="/telemetry/inverter",
            headers={},
        )
        response = lambda_handler(event, None)
        body = _parse_body(response)
        error_msg = body.get("error", "")
        # Must not contain internal details
        assert "dynamodb" not in error_msg.lower()
        assert "boto" not in error_msg.lower()
        assert "905418405543" not in error_msg
        assert "ona-platform" not in error_msg
        # Must be a non-empty generic message
        assert len(error_msg) > 0

    def test_error_response_body_format(self):
        """All error responses must have {"error": "..."} body."""
        for path in ["/telemetry/inverter", "/telemetry/site", "/bad/path"]:
            event = _make_event(path=path, headers={})
            response = lambda_handler(event, None)
            body = _parse_body(response)
            assert "error" in body, f"Missing 'error' key for path {path}"
            assert isinstance(body["error"], str)
            assert len(body["error"]) > 0


# ---------------------------------------------------------------------------
# validate_inverter_params tests
# ---------------------------------------------------------------------------

class TestValidateInverterParams:
    _valid_base = {
        "asset_id": "INV-001",
        "site_id": "SiteA",
        "start": "2025-01-01T00:00:00",
        "end": "2025-01-02T00:00:00",
    }

    def test_invalid_asset_id_special_chars_raises_validation_error(self):
        params = {**self._valid_base, "asset_id": "INV 001; DROP TABLE"}
        with pytest.raises(ValidationError, match="asset_id"):
            validate_inverter_params(params)

    def test_invalid_asset_id_slash_raises_validation_error(self):
        params = {**self._valid_base, "asset_id": "INV/001"}
        with pytest.raises(ValidationError, match="asset_id"):
            validate_inverter_params(params)

    def test_invalid_site_id_raises_validation_error(self):
        params = {**self._valid_base, "site_id": "Site A!"}
        with pytest.raises(ValidationError, match="site_id"):
            validate_inverter_params(params)

    def test_inverted_time_range_raises_validation_error(self):
        params = {
            **self._valid_base,
            "start": "2025-01-10T00:00:00",
            "end": "2025-01-01T00:00:00",
        }
        with pytest.raises(ValidationError, match="start"):
            validate_inverter_params(params)

    def test_time_range_exceeding_31_days_raises_validation_error(self):
        params = {
            **self._valid_base,
            "start": "2025-01-01T00:00:00",
            "end": "2025-02-15T00:00:00",  # 45 days
        }
        with pytest.raises(ValidationError, match="31"):
            validate_inverter_params(params)

    def test_limit_exceeding_1000_raises_validation_error(self):
        params = {**self._valid_base, "limit": "1001"}
        with pytest.raises(ValidationError, match="limit"):
            validate_inverter_params(params)

    def test_valid_params_return_normalised_dict(self):
        result = validate_inverter_params(self._valid_base)
        assert result["asset_id"] == "INV-001"
        assert result["site_id"] == "SiteA"
        assert result["resolution"] == "5min"
        assert result["limit"] == 100

    def test_valid_params_with_all_optional_fields(self):
        params = {
            **self._valid_base,
            "resolution": "daily",
            "limit": "500",
        }
        result = validate_inverter_params(params)
        assert result["resolution"] == "daily"
        assert result["limit"] == 500

    def test_exactly_31_days_is_valid(self):
        params = {
            **self._valid_base,
            "start": "2025-01-01T00:00:00",
            "end": "2025-02-01T00:00:00",  # exactly 31 days
        }
        result = validate_inverter_params(params)
        assert result["start"] == "2025-01-01T00:00:00"

    def test_limit_of_1000_is_valid(self):
        params = {**self._valid_base, "limit": "1000"}
        result = validate_inverter_params(params)
        assert result["limit"] == 1000


# ---------------------------------------------------------------------------
# validate_site_params tests
# ---------------------------------------------------------------------------

class TestValidateSiteParams:
    _valid_base = {
        "site_id": "SiteA",
        "start": "2025-01-01T00:00:00",
        "end": "2025-01-02T00:00:00",
    }

    def test_missing_site_id_raises_validation_error(self):
        params = {"start": "2025-01-01T00:00:00", "end": "2025-01-02T00:00:00"}
        with pytest.raises(ValidationError, match="site_id"):
            validate_site_params(params)

    def test_missing_start_raises_validation_error(self):
        params = {"site_id": "SiteA", "end": "2025-01-02T00:00:00"}
        with pytest.raises(ValidationError, match="start"):
            validate_site_params(params)

    def test_missing_end_raises_validation_error(self):
        params = {"site_id": "SiteA", "start": "2025-01-01T00:00:00"}
        with pytest.raises(ValidationError, match="end"):
            validate_site_params(params)

    def test_valid_params_return_normalised_dict(self):
        result = validate_site_params(self._valid_base)
        assert result["site_id"] == "SiteA"
        assert result["resolution"] == "5min"
        assert result["limit"] == 100


# ---------------------------------------------------------------------------
# check_rate_limit tests
# ---------------------------------------------------------------------------

class TestCheckRateLimit:
    def setup_method(self):
        """Clear rate limit counters before each test."""
        _counters.clear()

    def test_60_calls_succeed(self):
        """60 calls within the window should all succeed."""
        for i in range(60):
            check_rate_limit("test-key-60", max_requests=60, window_seconds=60)

    def test_61st_call_raises_rate_limit_error(self):
        """The 61st call within the window must raise RateLimitError."""
        for i in range(60):
            check_rate_limit("test-key-61", max_requests=60, window_seconds=60)
        with pytest.raises(RateLimitError):
            check_rate_limit("test-key-61", max_requests=60, window_seconds=60)

    def test_counter_resets_after_window_expires(self):
        """After the window expires, the counter should reset and allow new requests."""
        # Use a 1-second window for speed
        for i in range(5):
            check_rate_limit("test-key-reset", max_requests=5, window_seconds=1)

        # 6th call should fail
        with pytest.raises(RateLimitError):
            check_rate_limit("test-key-reset", max_requests=5, window_seconds=1)

        # Wait for the window to expire
        time.sleep(1.1)

        # Now the counter should have reset — this should succeed
        check_rate_limit("test-key-reset", max_requests=5, window_seconds=1)

    def test_different_keys_have_independent_counters(self):
        """Rate limits are per API key — different keys should not interfere."""
        for i in range(60):
            check_rate_limit("key-a", max_requests=60, window_seconds=60)
        # key-b should still have a fresh counter
        check_rate_limit("key-b", max_requests=60, window_seconds=60)


# ---------------------------------------------------------------------------
# CursorSerializer round-trip (via _decode_cursor)
# ---------------------------------------------------------------------------

class TestCursorRoundTrip:
    def _encode_cursor(self, asset_id: str, timestamp: str) -> str:
        """Encode a cursor the same way the SDK does."""
        payload = json.dumps({"asset_id": asset_id, "timestamp": timestamp})
        return base64.urlsafe_b64encode(payload.encode("utf-8")).rstrip(b"=").decode("ascii")

    def test_round_trip_basic(self):
        asset_id = "INV-001"
        timestamp = "2025-01-15T10:30:00"
        cursor = self._encode_cursor(asset_id, timestamp)
        decoded = _decode_cursor(cursor)
        assert decoded["asset_id"] == asset_id
        assert decoded["timestamp"] == timestamp

    def test_round_trip_with_special_safe_chars(self):
        asset_id = "INV-1000000054495190"
        timestamp = "2025-11-01T02:40:00"
        cursor = self._encode_cursor(asset_id, timestamp)
        decoded = _decode_cursor(cursor)
        assert decoded["asset_id"] == asset_id
        assert decoded["timestamp"] == timestamp

    def test_malformed_cursor_raises_validation_error(self):
        with pytest.raises(ValidationError, match="malformed|missing|Cursor"):
            _decode_cursor("not-valid-base64!!!")

    def test_cursor_missing_asset_id_raises_validation_error(self):
        payload = json.dumps({"timestamp": "2025-01-01T00:00:00"})
        cursor = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
        with pytest.raises(ValidationError, match="asset_id"):
            _decode_cursor(cursor)

    def test_cursor_missing_timestamp_raises_validation_error(self):
        payload = json.dumps({"asset_id": "INV-001"})
        cursor = base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode()
        with pytest.raises(ValidationError, match="timestamp"):
            _decode_cursor(cursor)

    def test_cursor_asset_id_mismatch_raises_validation_error(self):
        """validate_inverter_params must reject a cursor whose asset_id differs from the param."""
        cursor = self._encode_cursor("INV-OTHER", "2025-01-01T00:00:00")
        params = {
            "asset_id": "INV-001",
            "site_id": "SiteA",
            "start": "2025-01-01T00:00:00",
            "end": "2025-01-02T00:00:00",
            "cursor": cursor,
        }
        with pytest.raises(ValidationError, match="asset_id"):
            validate_inverter_params(params)
