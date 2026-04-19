#!/usr/bin/env python3
"""
OODA Terminal API Example

This example demonstrates how to use the OODA Terminal API to query and stream
OODA (Observe, Orient, Decide, Act) alerts from terminal devices.

Requirements:
- Set OODA_TERMINAL_ENDPOINT environment variable
- Set OODA_TERMINAL_API_KEY environment variable

Example usage:
    export OODA_TERMINAL_ENDPOINT="https://your-ooda-api.execute-api.af-south-1.amazonaws.com/prod"
    export OODA_TERMINAL_API_KEY="your-api-key-here"
    python ooda_terminal_example.py
"""

from datetime import datetime, timedelta
from ona_platform import OnaClient
from ona_platform.models.ooda import TimeRange

def main():
    """Main example function demonstrating OODA Terminal API usage."""
    
    # Initialize the client
    client = OnaClient()
    
    # Check if OODA Terminal API is configured
    if not client.config.ooda_terminal_endpoint:
        print("❌ OODA_TERMINAL_ENDPOINT environment variable not set")
        print("   Set it to your OODA Terminal API endpoint URL")
        return
    
    if not client.config.ooda_terminal_api_key:
        print("❌ OODA_TERMINAL_API_KEY environment variable not set")
        print("   Set it to your OODA Terminal API key")
        return
    
    print("🔗 OODA Terminal API Example")
    print(f"   Endpoint: {client.config.ooda_terminal_endpoint}")
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
        
        time_range = TimeRange(
            start=start_time.isoformat(),
            end=end_time.isoformat()
        )
        
        alerts = client.ooda_terminal.get_terminal_alerts(
            terminal_device_id=terminal_device_id,
            site_id=site_id,
            time_range=time_range,
            resolution="5min",
            limit=10
        )
        
        print(f"   Found {len(alerts)} alerts")
        for alert in alerts[:3]:  # Show first 3 alerts
            print(f"   • {alert.timestamp}: {alert.alert_severity.upper()} - {alert.message}")
        print()
        
        # 3. Query site alerts (all terminal devices)
        print("🏢 Querying site alerts (all terminal devices)...")
        site_alerts = client.ooda_terminal.get_site_alerts(
            site_id=site_id,
            time_range=time_range,
            resolution="5min",
            limit=5
        )
        
        total_alerts = sum(len(alerts) for alerts in site_alerts.values())
        print(f"   Found {total_alerts} alerts across {len(site_alerts)} terminal devices")
        for terminal_id, alerts in list(site_alerts.items())[:2]:  # Show first 2 devices
            print(f"   • {terminal_id}: {len(alerts)} alerts")
        print()
        
        # 4. Stream terminal alerts (demo for 30 seconds)
        print("📡 Streaming terminal alerts (30 seconds demo)...")
        print("   Press Ctrl+C to stop early")
        
        stream_count = 0
        start_stream = datetime.now()
        
        try:
            for alert in client.ooda_terminal.stream_terminal(
                terminal_device_id=terminal_device_id,
                site_id=site_id,
                polling_interval=5  # Poll every 5 seconds
            ):
                stream_count += 1
                print(f"   📨 {alert.timestamp}: {alert.alert_severity.upper()} - {alert.message}")
                
                # Stop after 30 seconds for demo
                if (datetime.now() - start_stream).seconds >= 30:
                    break
                    
        except KeyboardInterrupt:
            print("   Stream stopped by user")
        
        print(f"   Streamed {stream_count} alerts")
        print()
        
        # 5. Demonstrate cursor-based pagination
        print("📄 Demonstrating cursor-based pagination...")
        page_size = 3
        cursor = None
        page_num = 1
        
        while page_num <= 2:  # Show first 2 pages
            alerts = client.ooda_terminal.get_terminal_alerts(
                terminal_device_id=terminal_device_id,
                site_id=site_id,
                time_range=time_range,
                limit=page_size,
                cursor=cursor
            )
            
            if not alerts:
                break
                
            print(f"   Page {page_num}: {len(alerts)} alerts")
            for alert in alerts:
                print(f"     • {alert.timestamp}: {alert.message[:50]}...")
            
            # Use the last alert's cursor for next page
            cursor = alerts[-1].cursor if alerts else None
            page_num += 1
        
        print()
        print("✅ OODA Terminal API example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"   Type: {type(e).__name__}")


if __name__ == "__main__":
    main()