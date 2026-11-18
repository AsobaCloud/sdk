"""Behavioral tests for Issue #2: Model Observatory & PVInsight Client Support.

Verifies:
1. TerminalClient exposes get_model_observatory(customer_id, site=None) -> POST /terminal/model-observatory
2. OnaConfig supports pvinsight_endpoint and reads PVINSIGHT_API_URL from environment
3. PVInsightClient exposes analyze(detection, top_n, min_severity, job_id) -> POST /analyze
4. PVInsightClient exposes health() -> GET /health
5. OnaClient exposes client.pv_insight
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch
import pytest

from asoba.config import OnaConfig
from asoba import OnaClient


class TestIssue2ModelObservatoryBehavioral:
    """AC1: TerminalClient exposes get_model_observatory."""

    def test_get_model_observatory_calls_correct_endpoint_and_payload(self):
        """Given a TerminalClient, calling get_model_observatory sends POST to model-observatory."""
        config = OnaConfig(
            mode="edge",
            terminal_endpoint="http://localhost:8001",
        )
        client = OnaClient(config=config)

        expected_response = {
            "success": True,
            "customer_id": "Sibaya",
            "site": "Sibaya",
            "production_model_id": "lstm_sibaya_v1",
            "challengers": [
                {
                    "model_id": "lstm_sibaya_v1",
                    "is_production": True,
                    "r2": 0.88,
                    "nrmse": 0.09,
                    "windows": 1000,
                    "health_status": "HEALTHY",
                    "local": True,
                }
            ],
            "history": [],
        }

        with patch.object(client.terminal, "_post", return_value=expected_response) as mock_post:
            result = client.terminal.get_model_observatory(customer_id="Sibaya", site="Sibaya-SiteA")

            mock_post.assert_called_once_with(
                "model-observatory",
                {"customer_id": "Sibaya", "site": "Sibaya-SiteA"},
            )
            assert result["success"] is True
            assert result["production_model_id"] == "lstm_sibaya_v1"
            assert result["challengers"][0]["r2"] == 0.88


class TestIssue2PVInsightClientBehavioral:
    """AC3, AC4, AC5, AC6: PVInsight client and configuration."""

    def test_config_reads_pvinsight_api_url_from_env(self, monkeypatch):
        """Given PVINSIGHT_API_URL in env, OnaConfig.from_env() populates pvinsight_endpoint."""
        monkeypatch.setenv("ONA_MODE", "edge")
        monkeypatch.setenv("PVINSIGHT_API_URL", "http://localhost:8003")

        cfg = OnaConfig.from_env()
        assert hasattr(cfg, "pvinsight_endpoint"), "OnaConfig must have pvinsight_endpoint field"
        assert cfg.pvinsight_endpoint == "http://localhost:8003"

    def test_client_exposes_pv_insight_property(self):
        """Given an OnaClient, client.pv_insight returns PVInsightClient instance."""
        config = OnaConfig(
            mode="edge",
            pvinsight_endpoint="http://localhost:8003",
        )
        client = OnaClient(config=config)
        assert hasattr(client, "pv_insight"), "OnaClient must expose pv_insight property"
        assert client.pv_insight is not None

    def test_pv_insight_analyze_calls_post_analyze(self):
        """Calling analyze() sends POST /analyze with AnalyzeRequest payload."""
        config = OnaConfig(
            mode="edge",
            pvinsight_endpoint="http://localhost:8003",
        )
        client = OnaClient(config=config)

        detection = {
            "customer_id": "Sibaya",
            "asset_id": "INV-1000000054495190",
            "severity_label": "critical",
            "severity_score": 0.95,
        }
        mock_response = {
            "detection": detection,
            "llm_analysis": {
                "status": "completed",
                "recommendation": "Inspect DC disconnect switch and thermal fuse.",
                "cited_sources": [{"index": 1, "source": "Huawei_SUN2000_Manual.pdf"}],
            },
        }

        with patch("requests.post") as mock_req_post:
            mock_resp_obj = MagicMock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = mock_response
            mock_resp_obj.raise_for_status.return_value = None
            mock_req_post.return_value = mock_resp_obj

            res = client.pv_insight.analyze(
                detection=detection,
                top_n=5,
                min_severity="minor",
            )

            assert res["llm_analysis"]["status"] == "completed"
            mock_req_post.assert_called_once()
            args, kwargs = mock_req_post.call_args
            assert args[0] == "http://localhost:8003/analyze"
            payload = kwargs["json"]
            assert payload["detection"] == detection
            assert payload["top_n"] == 5
            assert payload["min_severity"] == "minor"

    def test_pv_insight_health_calls_get_health(self):
        """Calling health() sends GET /health."""
        config = OnaConfig(
            mode="edge",
            pvinsight_endpoint="http://localhost:8003",
        )
        client = OnaClient(config=config)

        with patch("requests.get") as mock_req_get:
            mock_resp_obj = MagicMock()
            mock_resp_obj.status_code = 200
            mock_resp_obj.json.return_value = {"status": "healthy", "service": "pvInsightService"}
            mock_resp_obj.raise_for_status.return_value = None
            mock_req_get.return_value = mock_resp_obj

            res = client.pv_insight.health()
            assert res["status"] == "healthy"
            assert res["service"] == "pvInsightService"
            mock_req_get.assert_called_once_with("http://localhost:8003/health", timeout=10)
