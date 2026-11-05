"""Behavioral tests for SDK edge transport mode (Issue #1).

These tests verify that OnaClient can communicate with edge-deployed
platform services via HTTP localhost endpoints instead of AWS Lambda.
They must FAIL against the current cloud-only implementation.
"""

from __future__ import annotations

import json
import sys
import importlib
from unittest.mock import patch, MagicMock
from types import ModuleType

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EDGE_ENDPOINTS = {
    "forecasting": "http://localhost:8002",
    "weather": "http://localhost:8004",
    "huawei_realtime": "http://localhost:8011",
    "huawei_historical": "http://localhost:8012",
    "training": "http://localhost:8001",
    "gap_detection": "http://localhost:8008",
    "standardization": "http://localhost:8009",
    "auth": "http://localhost:8013",
    "anomaly": "http://localhost:8005",
    "asset_intelligence": "http://localhost:8010",
    "solar_resource": "http://localhost:8006",
    "list_huawei_customers": "http://localhost:8007",
}


def make_edge_config():
    """Build an OnaConfig wired for edge mode with all edge endpoints."""
    from asoba.config import OnaConfig

    return OnaConfig(
        mode="edge",
        forecasting_endpoint=EDGE_ENDPOINTS["forecasting"],
        weather_endpoint=EDGE_ENDPOINTS["weather"],
        huawei_realtime_endpoint=EDGE_ENDPOINTS["huawei_realtime"],
        huawei_historical_endpoint=EDGE_ENDPOINTS["huawei_historical"],
        training_endpoint=EDGE_ENDPOINTS["training"],
        gap_detection_endpoint=EDGE_ENDPOINTS["gap_detection"],
        standardization_endpoint=EDGE_ENDPOINTS["standardization"],
        auth_endpoint=EDGE_ENDPOINTS["auth"],
        anomaly_endpoint=EDGE_ENDPOINTS["anomaly"],
        asset_intelligence_endpoint=EDGE_ENDPOINTS["asset_intelligence"],
        solar_resource_endpoint=EDGE_ENDPOINTS["solar_resource"],
        list_huawei_customers_endpoint=EDGE_ENDPOINTS["list_huawei_customers"],
    )


class FakeResponse:
    """Minimal stand-in for requests.Response."""

    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code
        self.text = json.dumps(json_data)

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


# ---------------------------------------------------------------------------
# EDGE-11: Config from env reads edge mode + endpoints
# ---------------------------------------------------------------------------

class TestConfigFromEnvEdgeMode:
    """EDGE-11: OnaConfig.from_env() with ONA_MODE=edge reads edge endpoints."""

    def test_config_from_env_edge_mode(self):
        env = {
            "ONA_MODE": "edge",
            "FORECAST_API_URL": "http://localhost:8002",
            "WEATHER_API_URL": "http://localhost:8004",
            "HUAWEI_REALTIME_URL": "http://localhost:8011",
            "HUAWEI_HISTORICAL_URL": "http://localhost:8012",
            "TRAINING_API_URL": "http://localhost:8001",
            "GAP_DETECTION_URL": "http://localhost:8008",
            "STANDARDIZATION_URL": "http://localhost:8009",
            "AUTH_API_URL": "http://localhost:8013",
            "ANOMALY_API_URL": "http://localhost:8005",
            "ASSET_INTELLIGENCE_URL": "http://localhost:8010",
            "SOLAR_RESOURCE_URL": "http://localhost:8006",
            "LIST_HUAWEI_CUSTOMERS_URL": "http://localhost:8007",
        }
        with patch.dict("os.environ", env, clear=False):
            from asoba.config import OnaConfig

            config = OnaConfig.from_env()
            assert config.mode == "edge"
            assert config.forecasting_endpoint == "http://localhost:8002"
            assert config.weather_endpoint == "http://localhost:8004"
            assert config.huawei_realtime_endpoint == "http://localhost:8011"
            assert config.auth_endpoint == "http://localhost:8013"

    def test_config_defaults_to_cloud(self):
        from asoba.config import OnaConfig

        config = OnaConfig()
        assert config.mode == "cloud"


# ---------------------------------------------------------------------------
# EDGE-1: Forecasting sends HTTP not Lambda in edge mode
# ---------------------------------------------------------------------------

class TestEdgeForecastingHttp:
    """EDGE-1: ForecastingClient sends HTTP POST in edge mode."""

    def test_edge_forecasting_sends_http_not_lambda(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_post(url, json=None, timeout=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({
                "site_id": "Sibaya",
                "forecasts": [{"hour": 1, "kWh_forecast": 5.2}],
            })

        with patch("requests.post", side_effect=fake_post):
            result = client.forecasting.get_site_forecast("Sibaya", forecast_hours=24)

        assert captured["url"] == "http://localhost:8002/forecast"
        assert captured["json"]["site_id"] == "Sibaya"
        assert captured["json"]["forecast_hours"] == 24
        assert "forecasts" in result
        assert result["forecasts"][0]["kWh_forecast"] == 5.2


# ---------------------------------------------------------------------------
# EDGE-2: Weather trigger sends HTTP in edge mode
# ---------------------------------------------------------------------------

class TestEdgeWeatherHttp:
    """EDGE-2: WeatherClient triggers update via HTTP in edge mode."""

    def test_edge_weather_trigger_http(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_post(url, json=None, timeout=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({"status": "accepted", "message": "Weather cache update started"})

        with patch("requests.post", side_effect=fake_post):
            result = client.weather.trigger_update()

        assert captured["url"] == "http://localhost:8004/run"
        assert result["status"] == "accepted"


# ---------------------------------------------------------------------------
# EDGE-3: Huawei realtime sends HTTP in edge mode
# ---------------------------------------------------------------------------

class TestEdgeHuaweiHttp:
    """EDGE-3: HuaweiClient.collect_realtime sends HTTP in edge mode."""

    def test_edge_huawei_realtime_http(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_post(url, json=None, timeout=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({"status": "ok", "records_collected": 10})

        with patch("requests.post", side_effect=fake_post):
            result = client.huawei.collect_realtime(plant_code="PLANT-001")

        assert captured["url"] == "http://localhost:8011/run"
        assert captured["json"]["plant_code"] == "PLANT-001"
        assert result["records_collected"] == 10


# ---------------------------------------------------------------------------
# EDGE-4: Gap detection sends HTTP in edge mode
# ---------------------------------------------------------------------------

class TestEdgeGapDetectionHttp:
    """EDGE-4: GapDetectionClient.detect_gaps sends HTTP in edge mode."""

    def test_edge_gap_detection_http(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_post(url, json=None, timeout=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({
                "customer_id": "Sibaya",
                "gaps": [],
                "total_missing_intervals": 0,
                "needs_backfill": False,
            })

        with patch("requests.post", side_effect=fake_post):
            result = client.gap_detection.detect_gaps(customer_id="Sibaya")

        assert captured["url"] == "http://localhost:8008/run"
        assert "customer_id" in captured["json"]
        assert result["needs_backfill"] is False


# ---------------------------------------------------------------------------
# EDGE-5: Auth login sends HTTP in edge mode
# ---------------------------------------------------------------------------

class TestEdgeAuthHttp:
    """EDGE-5: AuthClient.login sends HTTP POST in edge mode."""

    def test_edge_auth_login_http(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_post(url, json=None, timeout=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({"token": "fake-jwt-token", "user": {"username": "admin"}})

        with patch("requests.post", side_effect=fake_post):
            result = client.auth.login("admin", "admin")

        assert captured["url"] == "http://localhost:8013/api/auth/login"
        assert captured["json"]["username"] == "admin"
        assert captured["json"]["password"] == "admin"
        assert result["token"] == "fake-jwt-token"
        assert client.auth.get_token() == "fake-jwt-token"


# ---------------------------------------------------------------------------
# EDGE-6: Anomaly detection sends HTTP in edge mode
# ---------------------------------------------------------------------------

class TestEdgeAnomalyHttp:
    """EDGE-6: AnomalyClient.detect sends HTTP POST in edge mode."""

    def test_edge_anomaly_detection_http(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_post(url, json=None, timeout=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({
                "severity": "normal",
                "anomalies": [],
                "asset_id": "INV-001",
            })

        records = [{"timestamp": "2026-01-01T00:00:00Z", "power": 50.0, "temperature": 25.0}]

        with patch("requests.post", side_effect=fake_post):
            result = client.anomaly.detect(
                customer_id="Sibaya",
                asset_id="INV-001",
                records=records,
            )

        assert captured["url"] == "http://localhost:8005/detect"
        assert captured["json"]["customer_id"] == "Sibaya"
        assert captured["json"]["asset_id"] == "INV-001"
        assert captured["json"]["records"] == records
        assert result["severity"] == "normal"


# ---------------------------------------------------------------------------
# EDGE-7: Solar resource sends HTTP GET in edge mode
# ---------------------------------------------------------------------------

class TestEdgeSolarResourceHttp:
    """EDGE-7: SolarResourceClient.get_p50_p90 sends HTTP GET in edge mode."""

    def test_edge_solar_resource_http(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_get(url, timeout=None, params=None, **kwargs):
            if params:
                query = "&".join(f"{k}={v}" for k, v in params.items())
                captured["url"] = f"{url}?{query}"
            else:
                captured["url"] = url
            return FakeResponse({
                "p50": 1850.0,
                "p90": 1620.0,
                "psh": 5.1,
                "lat": -29.85,
                "lon": 31.02,
            })

        with patch("requests.get", side_effect=fake_get):
            result = client.solar_resource.get_p50_p90(lat=-29.85, lon=31.02)

        assert "lat=-29.85" in captured["url"]
        assert "lon=31.02" in captured["url"]
        assert "http://localhost:8006/api/v1/solar-resource" in captured["url"]
        assert result["p50"] == 1850.0


# ---------------------------------------------------------------------------
# EDGE-8: Enphase raises ConfigurationError in edge mode
# ---------------------------------------------------------------------------

class TestEdgeEnphaseConfigError:
    """EDGE-8: EnphaseClient raises ConfigurationError in edge mode."""

    def test_edge_enphase_raises_config_error(self):
        config = make_edge_config()
        from asoba.client import OnaClient
        from asoba.exceptions import ConfigurationError

        client = OnaClient(config=config)

        with pytest.raises(ConfigurationError, match="not available on edge"):
            client.enphase.collect_realtime(site_id="SIB-001")


# ---------------------------------------------------------------------------
# EDGE-9: Cloud mode unchanged — Lambda invocation preserved
# ---------------------------------------------------------------------------

class TestCloudModeUnchanged:
    """EDGE-9: OnaClient(mode='cloud') still uses Lambda invocation."""

    def test_cloud_mode_unchanged_lambda_behavior(self):
        from asoba.config import OnaConfig
        from asoba.client import OnaClient

        config = OnaConfig(mode="cloud")
        client = OnaClient(config=config)

        # Verify boto3 is the transport in cloud mode
        captured = {}

        original_invoke = client.forecasting.invoke_lambda

        def mock_invoke(function_name, payload, invocation_type="RequestResponse"):
            captured["function_name"] = function_name
            captured["payload"] = payload
            return {"forecasts": [{"kWh_forecast": 5.2}]}

        with patch.object(client.forecasting, "invoke_lambda", side_effect=mock_invoke):
            result = client.forecasting.get_site_forecast("Sibaya", forecast_hours=24)

        assert captured["function_name"] == "forecastingApi"
        assert captured["payload"]["site_id"] == "Sibaya"
        assert result["forecasts"][0]["kWh_forecast"] == 5.2


# ---------------------------------------------------------------------------
# EDGE-10: Terminal client works in edge mode (already HTTP-based)
# ---------------------------------------------------------------------------

class TestEdgeTerminalHttp:
    """EDGE-10: TerminalClient sends HTTP POST in edge mode (no AWS signing)."""

    def test_edge_terminal_list_assets_http(self):
        from asoba.config import OnaConfig
        from asoba.client import OnaClient

        config = OnaConfig(
            mode="edge",
            terminal_endpoint="http://localhost:8001",
        )
        client = OnaClient(config=config)

        captured = {}

        class FakeSession:
            headers = {}
            def post(self, url, json=None, timeout=None, **kwargs):
                captured["url"] = url
                captured["json"] = json
                return FakeResponse({"assets": [{"asset_id": "INV-001", "name": "Inverter 1"}]})

        from asoba.services.terminal import TerminalClient
        tc = TerminalClient(config)
        tc._session = FakeSession()
        client._terminal = tc

        result = client.terminal.list_assets(customer_id="Sibaya")

        assert captured["url"] == "http://localhost:8001/terminal/assets"
        assert captured["json"]["action"] == "list"
        assert captured["json"]["customer_id"] == "Sibaya"
        assert len(result) == 1
        assert result[0]["asset_id"] == "INV-001"


# ---------------------------------------------------------------------------
# EDGE-12: Training status sends HTTP GET in edge mode
# ---------------------------------------------------------------------------

class TestEdgeTrainingHttp:
    """EDGE-12: TrainingClient.get_training_status sends HTTP GET in edge mode."""

    def test_edge_training_status_http(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_get(url, timeout=None, params=None, **kwargs):
            if params:
                query = "&".join(f"{k}={v}" for k, v in params.items())
                captured["url"] = f"{url}?{query}"
            else:
                captured["url"] = url
            return FakeResponse({
                "customer_id": "Sibaya",
                "status": "RUNNING",
                "processing_job_name": "data-prep-Sibaya-001",
            })

        with patch("requests.get", side_effect=fake_get):
            result = client.training.get_training_status(job_id="Sibaya")

        assert "http://localhost:8001" in captured["url"]
        assert "training/status" in captured["url"]
        assert "customer_id=Sibaya" in captured["url"]
        assert result["status"] == "RUNNING"


# ---------------------------------------------------------------------------
# E2E: Full edge client path — no boto3 import, no Lambda
# ---------------------------------------------------------------------------

class TestEdgeE2E:
    """End-to-end: OnaClient(mode='edge') completes a forecast request
    without importing boto3 or invoking Lambda.
    """

    def test_edge_e2e_forecast_no_boto3_no_lambda(self):
        config = make_edge_config()
        from asoba.client import OnaClient

        client = OnaClient(config=config)

        captured = {}

        def fake_post(url, json=None, timeout=None, **kwargs):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse({
                "site_id": "Sibaya",
                "forecasts": [{"hour": 1, "kWh_forecast": 5.2}],
                "model_info": {"model_type": "lstm", "version": "v1"},
            })

        # Block boto3 import to prove it's not needed in edge mode
        original_boto3 = sys.modules.get("boto3")

        class Boto3Blocker:
            def find_module(self, name, path=None):
                if name == "boto3":
                    raise ImportError("boto3 must not be imported in edge mode")

        # Remove boto3 from cache to force re-import attempt
        if "boto3" in sys.modules:
            del sys.modules["boto3"]
        if "botocore" in sys.modules:
            del sys.modules["botocore"]

        sys.meta_path.insert(0, Boto3Blocker())
        try:
            with patch("requests.post", side_effect=fake_post):
                result = client.forecasting.get_site_forecast("Sibaya", forecast_hours=24)
        finally:
            sys.meta_path.pop(0)
            # Restore if it was there
            if original_boto3 is not None and "boto3" not in sys.modules:
                sys.modules["boto3"] = original_boto3

        assert captured["url"] == "http://localhost:8002/forecast"
        assert result["forecasts"][0]["kWh_forecast"] == 5.2
        assert result["model_info"]["model_type"] == "lstm"
