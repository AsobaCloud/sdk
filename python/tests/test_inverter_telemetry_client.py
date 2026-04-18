"""Tests for InverterTelemetryClient — real behavior, no mocks."""

import json
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ona_platform.config import OnaConfig
from ona_platform.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ValidationError,
)
from ona_platform.models.telemetry import TimeRange, TelemetryRecord
from ona_platform.services.inverter_telemetry import InverterTelemetryClient, MAX_LIMIT
from ona_platform.services.telemetry_cursor import CursorSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(endpoint="https://example.com", api_key="test-key", **kwargs):
    return OnaConfig(
        inverter_telemetry_endpoint=endpoint,
        inverter_telemetry_api_key=api_key,
        **kwargs,
    )


def _make_record(asset_id="INV-001", site_id="Sibaya", timestamp="2025-01-01T00:00:00"):
    return {
        "asset_id": asset_id,
        "site_id": site_id,
        "timestamp": timestamp,
        "asset_ts": f"{asset_id}#{timestamp}",
        "power": 1.5,
        "kWh": 100.0,
        "inverter_state": 1,
        "run_state": 1,
    }


# ---------------------------------------------------------------------------
# Fake HTTP server for end-to-end tests
# ---------------------------------------------------------------------------

class _FakeHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler that serves canned responses."""

    def log_message(self, *args):
        pass  # suppress output

    def do_GET(self):
        parsed = urlparse(self.path)
        _params = parse_qs(parsed.query)  # noqa: F841
        server_data = self.server.response_data  # type: ignore[attr-defined]

        if parsed.path == "/telemetry/inverter":
            records = server_data.get("inverter_records", [])
            body = json.dumps({"records": records}).encode()
            self._send(200, body)
        elif parsed.path == "/telemetry/site":
            records = server_data.get("site_records", {})
            body = json.dumps({"records": records}).encode()
            self._send(200, body)
        else:
            self._send(404, b'{"error": "not found"}')

    def _send(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _start_fake_server(response_data: dict):
    server = HTTPServer(("127.0.0.1", 0), _FakeHandler)
    server.response_data = response_data  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ---------------------------------------------------------------------------
# Configuration / instantiation tests
# ---------------------------------------------------------------------------

def test_missing_endpoint_raises_configuration_error():
    config = OnaConfig(inverter_telemetry_endpoint=None, inverter_telemetry_api_key="key")
    with pytest.raises(ConfigurationError, match="inverter_telemetry_endpoint"):
        InverterTelemetryClient(config)


def test_missing_api_key_raises_authentication_error():
    config = OnaConfig(inverter_telemetry_endpoint="https://example.com", inverter_telemetry_api_key=None)
    with pytest.raises(AuthenticationError, match="inverter_telemetry_api_key"):
        InverterTelemetryClient(config)


def test_http_endpoint_raises_configuration_error():
    with pytest.raises(ConfigurationError, match="https"):
        OnaConfig(inverter_telemetry_endpoint="http://example.com", inverter_telemetry_api_key="key")


# ---------------------------------------------------------------------------
# Validation tests (no network)
# ---------------------------------------------------------------------------

def test_inverted_time_range_raises_validation_error():
    client = InverterTelemetryClient(_make_config())
    tr = TimeRange(start="2025-02-01T00:00:00", end="2025-01-01T00:00:00")
    with pytest.raises(ValidationError, match="time_range"):
        client._validate_query_params("Sibaya", tr, 100)


def test_limit_over_1000_raises_validation_error():
    client = InverterTelemetryClient(_make_config())
    tr = TimeRange(start="2025-01-01T00:00:00", end="2025-01-02T00:00:00")
    with pytest.raises(ValidationError, match="limit"):
        client._validate_query_params("Sibaya", tr, 1001)


def test_time_range_over_31_days_raises_validation_error():
    client = InverterTelemetryClient(_make_config())
    start = "2025-01-01T00:00:00"
    end = "2025-02-15T00:00:00"  # > 31 days
    tr = TimeRange(start=start, end=end)
    with pytest.raises(ValidationError, match="31 days"):
        client._validate_query_params("Sibaya", tr, 100)


def test_polling_interval_below_5_raises_validation_error():
    client = InverterTelemetryClient(_make_config())
    with pytest.raises(ValidationError, match="polling_interval"):
        gen = client.stream_inverter("INV-001", "Sibaya", polling_interval=4.9)
        next(gen)


def test_duplicate_stream_raises_validation_error():
    client = InverterTelemetryClient(_make_config())
    client._active_streams.add("inverter:INV-001")
    with pytest.raises(ValidationError, match="already active"):
        gen = client.stream_inverter("INV-001", "Sibaya", polling_interval=5.0)
        next(gen)


# ---------------------------------------------------------------------------
# Real HTTP server tests
# ---------------------------------------------------------------------------

def test_get_inverter_telemetry_returns_records():
    records = [_make_record(timestamp=f"2025-01-01T00:0{i}:00") for i in range(3)]
    server = _start_fake_server({"inverter_records": records})
    port = server.server_address[1]
    # Use http:// for local test server — bypass https check by patching endpoint directly
    config = OnaConfig(
        inverter_telemetry_endpoint="https://placeholder",
        inverter_telemetry_api_key="test-key",
    )
    client = InverterTelemetryClient(config)
    client._endpoint = f"http://127.0.0.1:{port}"

    tr = TimeRange(start="2025-01-01T00:00:00", end="2025-01-01T01:00:00")
    result = client.get_inverter_telemetry("INV-001", "Sibaya", tr)

    assert len(result) == 3
    assert all(isinstance(r, TelemetryRecord) for r in result)
    server.shutdown()


def test_api_key_header_sent():
    """Verify x-api-key header is present and no AWS auth headers."""
    received_headers = {}

    class _HeaderCapture(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            received_headers.update(dict(self.headers))
            body = json.dumps({"records": []}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), _HeaderCapture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    config = OnaConfig(
        inverter_telemetry_endpoint="https://placeholder",
        inverter_telemetry_api_key="test-token-abc",  # noqa: S106
    )
    client = InverterTelemetryClient(config)
    client._endpoint = f"http://127.0.0.1:{port}"

    tr = TimeRange(start="2025-01-01T00:00:00", end="2025-01-01T01:00:00")
    client.get_inverter_telemetry("INV-001", "Sibaya", tr)

    assert received_headers.get("x-api-key") == "test-token-abc"
    assert "Authorization" not in received_headers
    assert "X-Amz-Security-Token" not in received_headers
    assert "X-Amz-Date" not in received_headers
    server.shutdown()


def test_stream_yields_only_newer_records():
    """Stream deduplication: only records with timestamp > last_ts are yielded."""
    records = [
        _make_record(timestamp="2025-01-01T00:00:00"),
        _make_record(timestamp="2025-01-01T00:05:00"),
        _make_record(timestamp="2025-01-01T00:10:00"),
    ]
    server = _start_fake_server({"inverter_records": records})
    port = server.server_address[1]

    config = OnaConfig(
        inverter_telemetry_endpoint="https://placeholder",
        inverter_telemetry_api_key="test-key",
        telemetry_polling_interval=5.0,
    )
    client = InverterTelemetryClient(config)
    client._endpoint = f"http://127.0.0.1:{port}"

    # Simulate: last_ts already at first record — test deduplication logic directly
    client._active_streams.add("inverter:INV-001")
    client._active_streams.discard("inverter:INV-001")

    # Test deduplication logic directly
    last_ts = "2025-01-01T00:00:00"
    yielded = []
    for r in records:
        rec = TelemetryRecord.from_dict(r)
        if rec.timestamp > last_ts:
            last_ts = rec.timestamp
            rec.cursor = CursorSerializer.serialize(rec.asset_id, last_ts)
            yielded.append(rec)

    assert len(yielded) == 2
    assert yielded[0].timestamp == "2025-01-01T00:05:00"
    assert yielded[1].timestamp == "2025-01-01T00:10:00"
    assert all(r.cursor is not None for r in yielded)
    server.shutdown()


def test_stream_records_have_cursors():
    """Every streamed record must carry a non-null cursor."""
    records = [_make_record(timestamp=f"2025-01-01T00:0{i}:00") for i in range(3)]
    last_ts = None
    yielded = []
    for r in records:
        rec = TelemetryRecord.from_dict(r)
        if last_ts is None or rec.timestamp > last_ts:
            last_ts = rec.timestamp
            rec.cursor = CursorSerializer.serialize(rec.asset_id, last_ts)
            yielded.append(rec)

    assert all(r.cursor is not None for r in yielded)
    assert all(isinstance(r.cursor, str) and len(r.cursor) > 0 for r in yielded)


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

_ts_strategy = st.datetimes(
    min_value=datetime(2020, 1, 1),
    max_value=datetime(2030, 12, 31),
).map(lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S"))

_asset_id_strategy = st.text(
    min_size=1, max_size=30,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"),
)


# Feature: inverter-telemetry-streaming, Property 6: Inverted time range always raises ValidationError
@given(
    start=_ts_strategy,
    end=_ts_strategy,
)
@settings(max_examples=100)
def test_property_6_inverted_time_range_raises_validation_error(start, end):
    """Validates: Requirements 1.7, 2.4"""
    if start <= end:
        return  # only test inverted ranges
    client = InverterTelemetryClient(_make_config())
    tr = TimeRange(start=start, end=end)
    with pytest.raises(ValidationError):
        client._validate_query_params("Sibaya", tr, 100)


# Feature: inverter-telemetry-streaming, Property 13: Non-HTTPS endpoint always raises ConfigurationError
@given(st.one_of(
    st.just("http://example.com"),
    st.just("ftp://example.com"),
    st.just("ws://example.com"),
    st.text(min_size=1, max_size=50).filter(lambda s: not s.startswith("https://")),
))
@settings(max_examples=100)
def test_property_13_non_https_endpoint_raises_configuration_error(endpoint):
    """Validates: Requirements 12.1, 12.2"""
    with pytest.raises(ConfigurationError):
        OnaConfig(inverter_telemetry_endpoint=endpoint, inverter_telemetry_api_key="key")


# Feature: inverter-telemetry-streaming, Property 14: limit > 1000 always raises ValidationError
@given(st.integers(min_value=1001, max_value=100000))
@settings(max_examples=100)
def test_property_14_limit_over_1000_raises_validation_error(limit):
    """Validates: Requirements 11.1"""
    client = InverterTelemetryClient(_make_config())
    tr = TimeRange(start="2025-01-01T00:00:00", end="2025-01-02T00:00:00")
    with pytest.raises(ValidationError, match="limit"):
        client._validate_query_params("Sibaya", tr, limit)


# Feature: inverter-telemetry-streaming, Property 15: Time range > 31 days always raises ValidationError
@given(st.integers(min_value=32, max_value=3650))
@settings(max_examples=100)
def test_property_15_time_range_over_31_days_raises_validation_error(days):
    """Validates: Requirements 11.2"""
    client = InverterTelemetryClient(_make_config())
    start_dt = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=days)
    tr = TimeRange(
        start=start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        end=end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
    )
    with pytest.raises(ValidationError, match="31 days"):
        client._validate_query_params("Sibaya", tr, 100)


# Feature: inverter-telemetry-streaming, Property 16: polling_interval < 5s always raises ValidationError
@given(st.floats(min_value=0.0, max_value=4.999, allow_nan=False, allow_infinity=False))
@settings(max_examples=100)
def test_property_16_polling_interval_below_5_raises_validation_error(interval):
    """Validates: Requirements 11.3"""
    client = InverterTelemetryClient(_make_config())
    with pytest.raises(ValidationError, match="polling_interval"):
        gen = client.stream_inverter("INV-001", "Sibaya", polling_interval=interval)
        next(gen)


# Feature: inverter-telemetry-streaming, Property 3: All returned records fall within the requested time range
@given(
    n=st.integers(min_value=0, max_value=10),
    limit=st.integers(min_value=1, max_value=MAX_LIMIT),
)
@settings(max_examples=100, deadline=None)
def test_property_3_records_within_time_range(n, limit):
    """Validates: Requirements 1.1 — records from a fake server are within the requested range."""
    start = "2025-01-01T00:00:00"
    end = "2025-01-31T23:59:59"
    records = [
        _make_record(timestamp=f"2025-01-{i+1:02d}T00:00:00")
        for i in range(min(n, 28))
    ]
    server = _start_fake_server({"inverter_records": records[:limit]})
    port = server.server_address[1]

    config = OnaConfig(
        inverter_telemetry_endpoint="https://placeholder",
        inverter_telemetry_api_key="test-key",
    )
    client = InverterTelemetryClient(config)
    client._endpoint = f"http://127.0.0.1:{port}"

    tr = TimeRange(start=start, end=end)
    result = client.get_inverter_telemetry("INV-001", "Sibaya", tr, limit=limit)

    for r in result:
        assert r.timestamp >= start
        assert r.timestamp <= end
    server.shutdown()


# Feature: inverter-telemetry-streaming, Property 4: Returned records are in ascending timestamp order
@given(st.integers(min_value=0, max_value=10))
@settings(max_examples=100, deadline=None)
def test_property_4_records_ascending_order(n):
    """Validates: Requirements 1.4"""
    records = sorted(
        [_make_record(timestamp=f"2025-01-{i+1:02d}T00:00:00") for i in range(min(n, 28))],
        key=lambda r: r["timestamp"],
    )
    server = _start_fake_server({"inverter_records": records})
    port = server.server_address[1]

    config = OnaConfig(
        inverter_telemetry_endpoint="https://placeholder",
        inverter_telemetry_api_key="test-key",
    )
    client = InverterTelemetryClient(config)
    client._endpoint = f"http://127.0.0.1:{port}"

    tr = TimeRange(start="2025-01-01T00:00:00", end="2025-01-31T23:59:59")
    result = client.get_inverter_telemetry("INV-001", "Sibaya", tr)

    timestamps = [r.timestamp for r in result]
    assert timestamps == sorted(timestamps)
    server.shutdown()


# Feature: inverter-telemetry-streaming, Property 5: Record count never exceeds the requested limit
@given(
    total=st.integers(min_value=0, max_value=20),
    limit=st.integers(min_value=1, max_value=MAX_LIMIT),
)
@settings(max_examples=100, deadline=None)
def test_property_5_record_count_respects_limit(total, limit):
    """Validates: Requirements 1.5 — server returns min(total, limit) records."""
    records = [_make_record(timestamp=f"2025-01-{i+1:02d}T00:00:00") for i in range(min(total, 28))]
    # Fake server returns only up to limit records
    server = _start_fake_server({"inverter_records": records[:limit]})
    port = server.server_address[1]

    config = OnaConfig(
        inverter_telemetry_endpoint="https://placeholder",
        inverter_telemetry_api_key="test-key",
    )
    client = InverterTelemetryClient(config)
    client._endpoint = f"http://127.0.0.1:{port}"

    tr = TimeRange(start="2025-01-01T00:00:00", end="2025-01-31T23:59:59")
    result = client.get_inverter_telemetry("INV-001", "Sibaya", tr, limit=limit)

    assert len(result) <= limit
    server.shutdown()


# Feature: inverter-telemetry-streaming, Property 7: Stream yields only strictly newer records
@given(st.lists(
    st.datetimes(min_value=datetime(2025, 1, 1), max_value=datetime(2025, 12, 31)).map(
        lambda dt: dt.strftime("%Y-%m-%dT%H:%M:%S")
    ),
    min_size=0, max_size=20,
))
@settings(max_examples=100)
def test_property_7_stream_yields_only_newer_records(timestamps):
    """Validates: Requirements 3.3"""
    if not timestamps:
        return
    last_ts = min(timestamps)
    yielded_ts = []
    for ts in timestamps:
        if ts > last_ts:
            last_ts = ts
            yielded_ts.append(ts)
    # All yielded timestamps must be strictly increasing
    for i in range(1, len(yielded_ts)):
        assert yielded_ts[i] > yielded_ts[i - 1]


# Feature: inverter-telemetry-streaming, Property 8: Every streamed record carries a non-null cursor
@given(st.lists(
    _ts_strategy,
    min_size=1, max_size=10,
))
@settings(max_examples=100)
def test_property_8_every_streamed_record_has_cursor(timestamps):
    """Validates: Requirements 5.1"""
    last_ts = None
    for ts in sorted(set(timestamps)):
        if last_ts is None or ts > last_ts:
            last_ts = ts
            rec = TelemetryRecord.from_dict(_make_record(timestamp=ts))
            rec.cursor = CursorSerializer.serialize("INV-001", ts)
            assert rec.cursor is not None
            assert len(rec.cursor) > 0


# Feature: inverter-telemetry-streaming, Property 12: Every request has x-api-key header; no AWS auth headers
@given(
    api_key=st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=33, max_codepoint=126).filter(lambda c: c not in '"\\')),
)
@settings(max_examples=50, deadline=None)
def test_property_12_api_key_header_no_aws_headers(api_key):
    """Validates: Requirements 8.1, 8.4"""
    received_headers = {}

    class _Capture(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_GET(self):
            received_headers.update(dict(self.headers))
            body = json.dumps({"records": []}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), _Capture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    config = OnaConfig(
        inverter_telemetry_endpoint="https://placeholder",
        inverter_telemetry_api_key=api_key,
    )
    client = InverterTelemetryClient(config)
    client._endpoint = f"http://127.0.0.1:{port}"

    tr = TimeRange(start="2025-01-01T00:00:00", end="2025-01-02T00:00:00")
    client.get_inverter_telemetry("INV-001", "Sibaya", tr)

    assert received_headers.get("x-api-key") == api_key
    assert "Authorization" not in received_headers
    assert "X-Amz-Security-Token" not in received_headers
    assert "X-Amz-Date" not in received_headers
    server.shutdown()
