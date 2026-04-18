"""
Unit tests for backend/inverter_telemetry_api/auth.py

Tests cover:
- AuthError raised when key not found
- AuthError raised when key has expired
- ForbiddenError raised when site_id not in permitted_site_ids
- Successful authentication returns permitted_site_ids
- Cache behaviour (TTL-based)
- Keys without expires_at are not rejected
"""
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# Clear module-level cache between tests
import backend.inverter_telemetry_api.auth as auth_module
from backend.inverter_telemetry_api.auth import (
    AuthError,
    ForbiddenError,
    authenticate,
)


def _make_record(
    api_key="test-key",
    permitted_site_ids=None,
    expires_at=None,
    client_id=1,
    region="af-south-1",
):
    record = {
        "api_key": api_key,
        "api_key_id": "key-id-001",
        "client_id": client_id,
        "region": region,
        "permitted_site_ids": ["SiteA", "SiteB"] if permitted_site_ids is None else permitted_site_ids,
    }
    if expires_at is not None:
        record["expires_at"] = expires_at
    return record


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the in-memory cache before each test."""
    auth_module._cache.clear()
    yield
    auth_module._cache.clear()


class TestAuthenticateKeyNotFound:
    def test_raises_auth_error_when_key_missing(self):
        with patch.object(auth_module, "_lookup_key", return_value=None):
            with pytest.raises(AuthError, match="not found"):
                authenticate("missing-key", "SiteA")


class TestAuthenticateExpiry:
    def test_raises_auth_error_when_key_expired(self):
        past = (datetime.now(tz=timezone.utc) - timedelta(hours=1)).isoformat()
        record = _make_record(expires_at=past)
        with patch.object(auth_module, "_lookup_key", return_value=record):
            with pytest.raises(AuthError, match="expired"):
                authenticate("test-key", "SiteA")

    def test_no_error_when_expires_at_is_in_future(self):
        future = (datetime.now(tz=timezone.utc) + timedelta(hours=1)).isoformat()
        record = _make_record(expires_at=future)
        with patch.object(auth_module, "_lookup_key", return_value=record):
            result = authenticate("test-key", "SiteA")
        assert "SiteA" in result

    def test_no_error_when_expires_at_absent(self):
        record = _make_record()  # no expires_at
        with patch.object(auth_module, "_lookup_key", return_value=record):
            result = authenticate("test-key", "SiteA")
        assert "SiteA" in result

    def test_invalid_expires_at_format_treated_as_expired(self):
        record = _make_record(expires_at="not-a-date")
        with patch.object(auth_module, "_lookup_key", return_value=record):
            with pytest.raises(AuthError, match="expired"):
                authenticate("test-key", "SiteA")


class TestAuthenticateSiteAuthorisation:
    def test_raises_forbidden_when_site_not_permitted(self):
        record = _make_record(permitted_site_ids=["SiteA", "SiteB"])
        with patch.object(auth_module, "_lookup_key", return_value=record):
            with pytest.raises(ForbiddenError):
                authenticate("test-key", "SiteC")

    def test_success_returns_permitted_site_ids(self):
        record = _make_record(permitted_site_ids=["SiteA", "SiteB"])
        with patch.object(auth_module, "_lookup_key", return_value=record):
            result = authenticate("test-key", "SiteA")
        assert result == ["SiteA", "SiteB"]

    def test_empty_permitted_site_ids_raises_forbidden(self):
        record = _make_record(permitted_site_ids=[])
        with patch.object(auth_module, "_lookup_key", return_value=record):
            with pytest.raises(ForbiddenError):
                authenticate("test-key", "SiteA")


class TestCacheBehaviour:
    def test_second_call_uses_cache(self):
        record = _make_record()
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": record}

        with patch.object(auth_module, "_get_dynamodb_table", return_value=mock_table):
            authenticate("test-key", "SiteA")
            authenticate("test-key", "SiteA")

        # DynamoDB should only be called once
        assert mock_table.get_item.call_count == 1

    def test_cache_expires_after_ttl(self):
        record = _make_record()
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": record}

        with patch.object(auth_module, "_get_dynamodb_table", return_value=mock_table):
            authenticate("test-key", "SiteA")

            # Manually expire the cache entry
            auth_module._cache["test-key"] = (
                record,
                time.monotonic() - 1,  # already expired
            )

            authenticate("test-key", "SiteA")

        # DynamoDB should be called twice (once fresh, once after cache expiry)
        assert mock_table.get_item.call_count == 2

    def test_dynamodb_error_raises_auth_error(self):
        mock_table = MagicMock()
        mock_table.get_item.side_effect = Exception("DynamoDB unavailable")

        with patch.object(auth_module, "_get_dynamodb_table", return_value=mock_table):
            with pytest.raises(AuthError, match="unavailable"):
                authenticate("test-key", "SiteA")
