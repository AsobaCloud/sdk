"""Behavioral tests for TerminalClient site intelligence methods."""

import pytest

from asoba.config import OnaConfig
from asoba.services.terminal import TerminalClient


def test_get_site_summary_returns_dict():
    """get_site_summary always returns a dict (may be empty if no snapshot yet)."""
    # Verify the method signature and return type contract without a network call
    # by exercising the response parsing path with a minimal _post stub.
    config = OnaConfig()

    client = TerminalClient(config)

    # Stub _post to return a realistic response shape
    def fake_post(path, body):
        assert path == "telemetry"
        assert body["action"] == "site-summary"
        return {
            "success": True,
            "site_id": body["site_id"],
            "summary": {
                "total_kWh_today": 1250.5,
                "fleet_pr_pct": 82.1,
                "battery": {
                    "avg_soh": 94.5,
                    "warranty_status": "in_warranty",
                },
                "soiling": {
                    "soiling_rate_pct_day": 0.15,
                    "detected_cleaning_events": [],
                    "recovery_gain_kwh_last_event": 125.5,
                },
                "prognostics": {
                    "battery_rul_days": 1200,
                    "health_score": 92.4,
                },
            },
        }

    client._post = fake_post
    summary = client.get_site_summary("test-site")

    assert summary["fleet_pr_pct"] == 82.1
    assert summary["battery"]["avg_soh"] == 94.5
    assert summary["soiling"]["soiling_rate_pct_day"] == 0.15
    assert summary["prognostics"]["health_score"] == 92.4


def test_get_site_summary_backward_compat_missing_optional_fields():
    """get_site_summary handles responses with no battery/soiling/prognostics."""
    config = OnaConfig()
    client = TerminalClient(config)

    def fake_post(path, body):
        return {
            "success": True,
            "summary": {
                "total_kWh_today": 1250.5,
                "fleet_pr_pct": 82.1,
            },
        }

    client._post = fake_post
    summary = client.get_site_summary("test-site")

    assert summary["total_kWh_today"] == 1250.5
    assert "soiling" not in summary
    assert "prognostics" not in summary
    assert "battery" not in summary


@pytest.mark.live
def test_get_site_summary_live():
    """Live: get_site_summary against api.asoba.co returns a dict."""
    from asoba import OnaClient
    client = OnaClient()
    summary = client.terminal.get_site_summary("Sibaya")
    assert isinstance(summary, dict)
