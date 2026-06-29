"""Tests for PartnerApiClient — real local HTTP server, no mocks.

Mirrors the pattern of test_inverter_telemetry_client.py: a small
BaseHTTPRequestHandler exposes the partner endpoints in-process so request
construction, header handling, ETag caching, and status-code mapping are
exercised end-to-end.

Coverage focus: SEP-062's new get_maintenance_schedule alongside the existing
three methods so the full Partner API surface stays in lockstep.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from ona_platform.config import OnaConfig
from ona_platform.exceptions import (
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
    ServiceUnavailableError,
)
from ona_platform.services.partner_api import PartnerApiClient

# ---------------------------------------------------------------------------
# Sample payloads matching the live S3 snapshot shapes
# ---------------------------------------------------------------------------

_SCHEDULE_PAYLOAD = {
    "site_id": "Sibaya",
    "generated_at": "2026-05-29T13:27:11.985596+00:00",
    "horizon": {"start": "2026-05-29", "end": "2026-08-27"},
    "tasks": [
        {
            "asset_id": "INV-1000000054495190",
            "task_type": "inspection",
            "reason": "33 anomalies detected in the last 2 days",
            "recommended_date": "2026-06-05",
            "estimated_duration_hours": 2.0,
            "priority": "High",
        }
    ],
    "summary": {
        "total_tasks": 1,
        "by_priority": {"High": 1},
        "by_task_type": {"inspection": 1},
        "by_asset": {"INV-1000000054495190": 1},
    },
}

_KPI_PAYLOAD = {
    "site_id": "Sibaya",
    "period": {"start": "2026-01-16", "end": "2026-01-17"},
    "generated_at": "2026-01-18T08:00:00Z",
    "system": {"rated_capacity_kw": 330.0, "device_count": 1},
    "energy_balance": {
        "consumption_kwh": 5000.0,
        "solar_production_kwh": 1200.0,
        "grid_purchases_kwh": 3800.0,
        "solar_offset_pct": 24.0,
    },
    "performance": {
        "system_pr": 0.78,
        "pr_target": 0.80,
        "pr_status": "Below Target",
        "true_uptime_pct": 98.5,
        "state_uptime_pct": 99.0,
        "availability_pct": 98.2,
        "availability_target": 0.98,
    },
    "ear": {
        "energy_lost_kwh": 54.2,
        "energy_lost_pct": 4.5,
        "capacity_utilization_pct": 74.1,
        "recovery_potential_kwh": {
            "50pct": 27.1,
            "75pct": 40.6,
            "100pct": 54.2,
        },
        "value_lost_zar": 276.4,
        "realized_savings_zar": 6120.0,
        "annual_projection_zar": 1146878.0,
    },
    "financial": {
        "tariff_currency": "ZAR",
        "shortfall_cost_zar": 276.4,
        "realized_savings_zar": 6120.0,
        "total_potential_value_zar": 6396.4,
        "tou_breakdown": {},
    },
    "battery": {
        "avg_soc": 82.5,
        "avg_soh": 99.1,
        "total_capacity_kwh": 13.5,
        "warranty_status": "in_warranty",
        "throughput_kwh": 450.2,
    },
}
_SIGNALS_PAYLOAD = {"site_id": "Sibaya", "signals": []}
_FORECAST_PAYLOAD = {"site_id": "Sibaya", "horizon_hours": 24, "intervals": []}


# ---------------------------------------------------------------------------
# Fake HTTP server
# ---------------------------------------------------------------------------


class _PartnerApiHandler(BaseHTTPRequestHandler):
    """Handler that routes Partner API paths to the right canned payload and
    supports ETag conditional GETs."""

    # Per-test routing knobs are class-level so the test can mutate them
    # without re-binding the handler.
    status_code = 200
    etag_value = "etag-v1"
    last_path = None
    last_query = None
    last_if_none_match = None
    call_count = 0

    def log_message(self, *_args, **_kwargs):  # silence test output noise
        return

    def do_GET(self):  # noqa: N802
        type(self).call_count += 1
        parsed = urlparse(self.path)
        type(self).last_path = parsed.path
        type(self).last_query = parse_qs(parsed.query)
        type(self).last_if_none_match = self.headers.get("If-None-Match")

        # Status-code override (for error-mapping tests) short-circuits
        if type(self).status_code != 200:
            self.send_response(type(self).status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"upstream"}')
            return

        # ETag cache hit
        if type(self).last_if_none_match == type(self).etag_value:
            self.send_response(304)
            self.end_headers()
            return

        body_by_path = {
            "/kpi-rollup": _KPI_PAYLOAD,
            "/maintenance-signals": _SIGNALS_PAYLOAD,
            "/forecast-snapshot": _FORECAST_PAYLOAD,
            "/maintenance-schedule": _SCHEDULE_PAYLOAD,
        }
        body = body_by_path.get(parsed.path)
        if body is None:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return

        encoded = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("ETag", type(self).etag_value)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _start_server():
    server = HTTPServer(("127.0.0.1", 0), _PartnerApiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _reset_handler():
    _PartnerApiHandler.status_code = 200
    _PartnerApiHandler.etag_value = "etag-v1"
    _PartnerApiHandler.last_path = None
    _PartnerApiHandler.last_query = None
    _PartnerApiHandler.last_if_none_match = None
    _PartnerApiHandler.call_count = 0


@pytest.fixture
def server():
    _reset_handler()
    srv = _start_server()
    yield srv
    srv.shutdown()
    srv.server_close()


def _make_client(server, api_key="test-key"):
    host, port = server.server_address
    config = OnaConfig(
        partner_api_endpoint=f"https://{host}:{port}",
        partner_api_key=api_key,
    )
    # Point at the actual HTTP server (the OnaConfig requires https:// for
    # validation; we override the live endpoint to http for the local test).
    client = PartnerApiClient(config)
    client._endpoint = f"http://{host}:{port}"
    return client


# ---------------------------------------------------------------------------
# Config + auth guards
# ---------------------------------------------------------------------------


class TestConfigGuards:
    def test_eh1_missing_endpoint_raises_configuration_error(self):
        config = OnaConfig(partner_api_endpoint=None, partner_api_key="k")
        with pytest.raises(ConfigurationError):
            PartnerApiClient(config)

    def test_eh1_non_https_endpoint_raises_configuration_error(self):
        # OnaConfig validates the https:// requirement at construction time;
        # PartnerApiClient only sees configs that already passed that check.
        with pytest.raises(ConfigurationError):
            OnaConfig(partner_api_endpoint="http://api.example.com", partner_api_key="k")

    def test_eh2_missing_api_key_raises_auth_error(self):
        config = OnaConfig(partner_api_endpoint="https://api.example.com", partner_api_key=None)
        with pytest.raises(AuthenticationError):
            PartnerApiClient(config)


# ---------------------------------------------------------------------------
# get_maintenance_schedule — SEP-062
# ---------------------------------------------------------------------------


class TestMaintenanceSchedule:
    def test_hp1_get_maintenance_schedule_returns_payload(self, server):
        client = _make_client(server)
        result = client.get_maintenance_schedule(site_id="Sibaya")

        assert result == _SCHEDULE_PAYLOAD
        assert _PartnerApiHandler.last_path == "/maintenance-schedule"
        assert _PartnerApiHandler.last_query == {"site_id": ["Sibaya"]}

    def test_ib1_path_is_maintenance_schedule(self, server):
        client = _make_client(server)
        client.get_maintenance_schedule(site_id="CapeTown")
        assert _PartnerApiHandler.last_path == "/maintenance-schedule"

    def test_ib2_site_id_in_query_string(self, server):
        client = _make_client(server)
        client.get_maintenance_schedule(site_id="CapeTown")
        assert _PartnerApiHandler.last_query == {"site_id": ["CapeTown"]}

    def test_hp1_since_param_threads_through(self, server):
        client = _make_client(server)
        client.get_maintenance_schedule(site_id="Sibaya", since="2026-05-01T00:00:00")
        assert _PartnerApiHandler.last_query == {
            "site_id": ["Sibaya"],
            "since": ["2026-05-01T00:00:00"],
        }

    def test_hp3_etag_cache_hit_returns_cached_payload(self, server):
        client = _make_client(server)
        first = client.get_maintenance_schedule(site_id="Sibaya")
        second = client.get_maintenance_schedule(site_id="Sibaya")
        assert first == second
        # Both calls hit the server (the 2nd sent If-None-Match and got 304)
        assert _PartnerApiHandler.call_count == 2
        assert _PartnerApiHandler.last_if_none_match == "etag-v1"


# ---------------------------------------------------------------------------
# Status-code mapping (shared across all four methods)
# ---------------------------------------------------------------------------


class TestStatusMapping:
    def test_eh3_429_raises_rate_limit(self, server):
        _PartnerApiHandler.status_code = 429
        client = _make_client(server)
        with pytest.raises(RateLimitError):
            client.get_maintenance_schedule(site_id="Sibaya")

    def test_eh4_500_raises_service_unavailable(self, server):
        _PartnerApiHandler.status_code = 500
        client = _make_client(server)
        with pytest.raises(ServiceUnavailableError):
            client.get_maintenance_schedule(site_id="Sibaya")

    def test_eh2_401_raises_auth_error(self, server):
        _PartnerApiHandler.status_code = 401
        client = _make_client(server)
        with pytest.raises(AuthenticationError):
            client.get_maintenance_schedule(site_id="Sibaya")

    def test_eh2_403_raises_auth_error(self, server):
        _PartnerApiHandler.status_code = 403
        client = _make_client(server)
        with pytest.raises(AuthenticationError):
            client.get_maintenance_schedule(site_id="Sibaya")


# ---------------------------------------------------------------------------
# Regression: existing three methods still work
# ---------------------------------------------------------------------------


class TestExistingMethodsStillWork:
    def test_inv_get_kpi_rollup(self, server):
        client = _make_client(server)
        assert client.get_kpi_rollup(site_id="Sibaya") == _KPI_PAYLOAD

    def test_inv_get_maintenance_signals(self, server):
        client = _make_client(server)
        assert client.get_maintenance_signals(site_id="Sibaya") == _SIGNALS_PAYLOAD

    def test_inv_get_forecast_snapshot(self, server):
        client = _make_client(server)
        assert client.get_forecast_snapshot(site_id="Sibaya") == _FORECAST_PAYLOAD
