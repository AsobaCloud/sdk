"""Tests for TerminalClient — battery health and warranty tracking."""

from unittest.mock import MagicMock
from datetime import date, timedelta
from ona_platform.services.terminal import TerminalClient
from ona_platform.config import OnaConfig
from ona_platform.exceptions import ResourceNotFoundError

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
