#!/usr/bin/env python3
"""
OODA Terminal API Example

This example demonstrates how to use the OODA Terminal API to query and stream
OODA (Observe, Orient, Decide, Act) alerts from terminal devices.

Requirements:
- Set ASOBA_API_KEY environment variable

Example usage:
    export ASOBA_API_KEY="your-api-key-here"
    python ooda_terminal_example.py
"""

from datetime import datetime, timedelta

from asoba import OnaClient
from asoba.models.ooda import TimeRange


def main():
    """Main example function demonstrating OODA Terminal API usage."""

    # Initialize the client — picks up ASOBA_API_KEY from environment
    client = OnaClient()

    if not client.config.api_key:
        print("❌ ASOBA_API_KEY environment variable not set")
        print("   Set it to your Asoba API key")
        return

    print("🔗 OODA Terminal API Example")
    print(f"   Endpoint: {client.config.ooda_endpoint}")
    print()

    # Example site and terminal device
    site_id = "Sibaya"
    terminal_device_id = "TERM-1000000054495190"

    try:
        # 1. Discover available data period
        print("📊 Discovering available data period...")
        data_period = client.ooda_terminal.get_data_period(site_id=site_id)
        print(f"   Site: {data_period.site_id}")
        print(f"   First record: {data_period.first_record}")
        print(f"   Last record: {data_period.last_record}")
        print()

        # 2. Query terminal alerts for the last 24 hours
        print("🔍 Querying terminal alerts (last 24 hours)...")
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        time_range = TimeRange(start=start_time.isoformat(), end=end_time.isoformat())

        alerts = client.ooda_terminal.get_terminal_alerts(
            terminal_device_id=terminal_device_id,
            site_id=site_id,
            time_range=time_range,
            resolution="5min",
            limit=10,
        )
        print(f"   Found {len(alerts)} alerts")
        for alert in alerts[:3]:
            print(f"   {alert.timestamp}: {alert.alert_severity.upper()} - {alert.message}")
        print()

        # 3. Query site alerts (all terminal devices)
        print("🔍 Querying site alerts...")
        site_alerts = client.ooda_terminal.get_site_alerts(
            site_id=site_id,
            time_range=time_range,
            resolution="5min",
            limit=5,
        )
        total = sum(len(a) for a in site_alerts.values())
        print(f"   Found {total} alerts across {len(site_alerts)} terminal devices")
        print()

        # 4. Stream live terminal alerts (one cycle)
        print("📡 Streaming live terminal alerts (one poll)...")
        for alert in client.ooda_terminal.stream_terminal(
            terminal_device_id=terminal_device_id,
            site_id=site_id,
            polling_interval=5,
        ):
            print(f"   {alert.timestamp}: {alert.alert_severity.upper()} - {alert.message}")
            break

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
