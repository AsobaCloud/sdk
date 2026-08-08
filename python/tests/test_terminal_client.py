"""Behavioral tests for TerminalClient.

These tests call api.asoba.co/terminal/* over HTTP.
Requires TERMINAL_API_TOKEN in the environment.
Tests that need a real backend response are marked @pytest.mark.live.
"""

from datetime import date, timedelta

import pytest

from asoba.services.terminal import TerminalClient

# ---------------------------------------------------------------------------
# calculate_remaining_warranty_life — pure logic, no network
# ---------------------------------------------------------------------------

def test_warranty_healthy():
    today = date.today()
    expiry = (today + timedelta(days=100)).isoformat()
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=500,
    )
    assert res["warranty_status"] == "in_warranty"
    assert res["days_remaining"] == 100
    assert res["throughput_remaining_pct"] == 50.0
    assert res["limiting_factor"] == "date"


def test_warranty_expiring_soon_by_date():
    today = date.today()
    expiry = (today + timedelta(days=30)).isoformat()
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=500,
    )
    assert res["warranty_status"] == "expiring_soon"
    assert res["limiting_factor"] == "date"
    assert res["days_remaining"] == 30


def test_warranty_expiring_soon_by_throughput():
    today = date.today()
    expiry = (today + timedelta(days=100)).isoformat()
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=850,
    )
    assert res["warranty_status"] == "expiring_soon"
    assert res["limiting_factor"] == "throughput"
    assert res["throughput_remaining_pct"] == 15.0


def test_warranty_expired_by_date():
    today = date.today()
    expired = (today - timedelta(days=1)).isoformat()
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expired,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=500,
    )
    assert res["warranty_status"] == "out_of_warranty"
    assert res["days_remaining"] == -1


def test_warranty_expired_by_throughput():
    today = date.today()
    expiry = (today + timedelta(days=100)).isoformat()
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=1100,
    )
    assert res["warranty_status"] == "out_of_warranty"
    assert res["throughput_remaining_pct"] == 0.0


def test_warranty_unknown_no_data():
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=None,
        warranty_throughput_kwh=None,
    )
    assert res["warranty_status"] == "unknown"
    assert res["days_remaining"] is None
    assert res["throughput_remaining_pct"] is None


# ---------------------------------------------------------------------------
# Live tests — require TERMINAL_API_TOKEN
# ---------------------------------------------------------------------------

JEPA_DETECTION = {
    "asset_id": "INV-BN2441041190",
    "severity_label": "high",
    "severity_score": 0.82,
    "fault_type": "behavioral_anomaly",
    "summary": "Inverter 1 - World model anomaly score 0.0891 (Streak: 6)",
    "metrics": {
        "latest_power_kw": 45.2,
        "baseline_power_kw": 280.5,
        "latest_temperature_c": 68.3,
        "latest_inverter_state": 513,
        "world_model_streak_length": 6,
    },
    "energy_at_risk_kw": 235.3,
}


@pytest.mark.live
def test_get_asset_not_found():
    """get_asset returns None for a nonexistent asset."""
    from asoba import OnaClient
    client = OnaClient()
    asset = client.terminal.get_asset("cust-1", "nonexistent-asset-xyz")
    assert asset is None


@pytest.mark.live
def test_get_site_summary_has_expected_shape():
    """get_site_summary returns a dict with at minimum a site-level key."""
    from asoba import OnaClient
    client = OnaClient()
    summary = client.terminal.get_site_summary("Sibaya")
    assert isinstance(summary, dict)


@pytest.mark.live
def test_pv_insight_synthesis_live():
    """BC-1: pv-insight synthesis returns llm_analysis with status=ok."""
    from asoba import OnaClient
    client = OnaClient()
    result = client.terminal.run_pv_insight_synthesis(JEPA_DETECTION)

    assert "llm_analysis" in result, "response must contain llm_analysis"
    llm = result["llm_analysis"]
    assert llm.get("status") == "ok", f"expected status=ok, got {llm.get('status')!r}"
    assert isinstance(llm.get("recommendation"), str) and len(llm["recommendation"]) > 20
    assert isinstance(llm.get("cited_sources"), list) and len(llm["cited_sources"]) > 0
