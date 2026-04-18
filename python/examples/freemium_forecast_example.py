#!/usr/bin/env python3
"""
Freemium Forecast Example

Generate a 24-hour solar energy forecast from a CSV file.
No API key required.

Usage:
    python3 freemium_forecast_example.py

The script creates a sample CSV and submits it to the freemium forecast endpoint.
"""

import csv
import tempfile
import os
from ona_platform import OnaClient


def create_sample_csv(path: str) -> None:
    """Write a minimal sample CSV with historical solar production data."""
    rows = [
        ("Timestamp", "Power (kW)"),
        ("2025-12-01T00:00:00Z", "0"),
        ("2025-12-01T01:00:00Z", "0"),
        ("2025-12-01T05:00:00Z", "10.5"),
        ("2025-12-01T06:00:00Z", "55.2"),
        ("2025-12-01T07:00:00Z", "120.7"),
        ("2025-12-01T08:00:00Z", "380.4"),
        ("2025-12-01T09:00:00Z", "720.1"),
        ("2025-12-01T10:00:00Z", "1100.3"),
        ("2025-12-01T11:00:00Z", "1450.8"),
        ("2025-12-01T12:00:00Z", "1850.2"),
        ("2025-12-01T13:00:00Z", "1780.5"),
        ("2025-12-01T14:00:00Z", "1620.9"),
        ("2025-12-01T15:00:00Z", "1200.4"),
        ("2025-12-01T16:00:00Z", "750.6"),
        ("2025-12-01T17:00:00Z", "320.1"),
        ("2025-12-01T18:00:00Z", "80.3"),
        ("2025-12-01T19:00:00Z", "0"),
        ("2025-12-01T20:00:00Z", "0"),
    ]
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def main():
    client = OnaClient()

    # Create a temporary sample CSV
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
        tmp_path = tmp.name
    create_sample_csv(tmp_path)

    print("=== Freemium Forecast Example ===")
    print(f"CSV: {tmp_path}")
    print()

    try:
        result = client.freemium_forecast.get_forecast(
            csv_path=tmp_path,
            email="demo@example.com",
            site_name="Demo Solar Site",
            location="Durban",
        )

        forecast = result["forecast"]
        print(f"Site:          {forecast['site_name']}")
        print(f"Location:      {forecast['location']}")
        print(f"Model type:    {forecast['model_type']}")
        print(f"Generated at:  {forecast['generated_at']}")
        print()

        summary = forecast.get("summary", {})
        print("=== Summary ===")
        print(f"  Total 24h:   {summary.get('total_kwh_24h', 'N/A')} kWh")
        print(f"  Peak hour:   {summary.get('peak_hour', 'N/A')}")
        print(f"  Peak output: {summary.get('peak_kwh', 'N/A')} kWh")
        print()

        print("=== Hourly Forecast (first 6 hours) ===")
        for point in forecast["forecasts"][:6]:
            print(
                f"  {point['timestamp']}  "
                f"{point['kWh_forecast']:>8.1f} kWh  "
                f"confidence={point['confidence']:.0%}"
            )

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
