"""Tests for TerminalClient — battery health and warranty tracking."""

import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta
from asoba.services.terminal import TerminalClient
from asoba.config import OnaConfig
from asoba.exceptions import ResourceNotFoundError

def test_calculate_remaining_warranty_life():
    today = date.today()
    expiry = (today + timedelta(days=100)).isoformat()
    
    # Case 1: Healthy battery, well within warranty
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=500
    )
    assert res["warranty_status"] == "in_warranty"
    assert res["days_remaining"] == 100
    assert res["throughput_remaining_pct"] == 50.0
    assert res["limiting_factor"] == "date"

    # Case 2: Expiring soon due to date (< 90 days)
    expiry_soon = (today + timedelta(days=30)).isoformat()
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry_soon,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=500
    )
    assert res["warranty_status"] == "expiring_soon"
    assert res["limiting_factor"] == "date"
    assert res["days_remaining"] == 30

    # Case 3: Expiring soon due to throughput (> 80% used)
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=850
    )
    assert res["warranty_status"] == "expiring_soon"
    assert res["limiting_factor"] == "throughput"
    assert res["throughput_remaining_pct"] == 15.0

    # Case 4: Out of warranty due to date
    expired = (today - timedelta(days=1)).isoformat()
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expired,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=500
    )
    assert res["warranty_status"] == "out_of_warranty"
    assert res["days_remaining"] == -1
    
    # Case 5: Out of warranty due to throughput
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=expiry,
        warranty_throughput_kwh=1000,
        current_throughput_kwh=1100
    )
    assert res["warranty_status"] == "out_of_warranty"
    assert res["throughput_remaining_pct"] == 0.0

    # Case 6: Unknown status (missing data)
    res = TerminalClient.calculate_remaining_warranty_life(
        warranty_expiry_date=None,
        warranty_throughput_kwh=None
    )
    assert res["warranty_status"] == "unknown"
    assert res["days_remaining"] is None
    assert res["throughput_remaining_pct"] is None

def test_get_asset_not_found():
    config = OnaConfig(aws_region="af-south-1")
    client = TerminalClient(config)
    # Mock invoke_lambda to raise ResourceNotFoundError
    client.invoke_lambda = MagicMock(side_effect=ResourceNotFoundError("Not found"))
    
    asset = client.get_asset("cust-1", "asset-1")
    assert asset is None

def test_get_asset_success():
    config = OnaConfig(aws_region="af-south-1")
    client = TerminalClient(config)
    mock_asset = {
        "asset_id": "asset-1",
        "capacity_kwh": 13.5,
        "warranty_expiry_date": "2030-01-01"
    }
    client.invoke_lambda = MagicMock(return_value=mock_asset)
    
    asset = client.get_asset("cust-1", "asset-1")
    assert asset["asset_id"] == "asset-1"
    assert asset["capacity_kwh"] == 13.5

def test_get_site_summary():
    config = OnaConfig(aws_region="af-south-1")
    client = TerminalClient(config)
    mock_res = {
        "site_id": "site-1",
        "fleet_metrics": {},
        "battery": {
            "avg_soc": 85.0,
            "avg_soh": 98.2,
            "total_capacity_kwh": 27.0,
            "warranty_status": "in_warranty"
        }
    }
    client.invoke_lambda = MagicMock(return_value=mock_res)
    
    summary = client.get_site_summary("site-1")
    assert "battery" in summary
    assert summary["battery"]["avg_soc"] == 85.0
    assert summary["battery"]["avg_soh"] == 98.2


# ---------------------------------------------------------------------------
# pv-insight synthesis — JEPA fixture (copied from platform/ui/tests/test_pv_insight_e2e_behavioral.js)
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


# ---------------------------------------------------------------------------
# BC-1 — live end-to-end test
# Run with: pytest -m live python/tests/test_terminal_client.py::test_pv_insight_synthesis_live
# Requires: env AWS credentials + terminalApi Lambda accessible
# ---------------------------------------------------------------------------

@pytest.mark.live
def test_pv_insight_synthesis_live():
    """BC-1: Live call to terminalApi pv-insight action via OnaClient.

    Pass criteria (copied from platform/ui/tests/test_pv_insight_e2e_behavioral.js Step 3):
    - llm_analysis is present in the response
    - llm_analysis['status'] == 'ok'
    - llm_analysis['recommendation'] is a string with length > 20
    - llm_analysis['cited_sources'] is a list with length > 0
    """
    from asoba import OnaClient  # matches terminal_ooda_example.py import

    client = OnaClient()  # reads AWS creds from env; default timeout 120s
    result = client.terminal.run_pv_insight_synthesis(JEPA_DETECTION)

    assert "llm_analysis" in result, "response must contain llm_analysis"
    llm = result["llm_analysis"]
    assert llm.get("status") == "ok", f"llm_analysis.status expected 'ok', got {llm.get('status')!r}"
    assert isinstance(llm.get("recommendation"), str) and len(llm["recommendation"]) > 20, (
        "llm_analysis.recommendation must be a string with length > 20"
    )
    assert isinstance(llm.get("cited_sources"), list) and len(llm["cited_sources"]) > 0, (
        "llm_analysis.cited_sources must be a non-empty list"
    )


# ---------------------------------------------------------------------------
# Secondary — error-path tests (not equal weight to done)
# ---------------------------------------------------------------------------

def test_pv_insight_synthesis_missing_detection_raises():
    """Missing detection should raise via SDK error handling (mock 400 from Lambda)."""
    config = OnaConfig(aws_region="af-south-1")
    client = TerminalClient(config)

    from asoba.exceptions import ValidationError
    client.invoke_lambda = MagicMock(
        side_effect=ValidationError("detection is required")
    )

    with pytest.raises(ValidationError):
        client.run_pv_insight_synthesis(detection=None)


def test_pv_insight_synthesis_invalid_severity_label_raises():
    """detection with invalid severity_label should raise via SDK error handling (mock 400)."""
    config = OnaConfig(aws_region="af-south-1")
    client = TerminalClient(config)

    bad_detection = dict(JEPA_DETECTION, severity_label="nope")

    from asoba.exceptions import ValidationError
    client.invoke_lambda = MagicMock(
        side_effect=ValidationError("invalid severity_label")
    )

    with pytest.raises(ValidationError):
        client.run_pv_insight_synthesis(detection=bad_detection)
