"""Complete workflow example using multiple services."""

from ona_platform import OnaClient


def main():
    """Demonstrate a complete workflow across multiple services."""

    # Initialize client
    client = OnaClient()
    customer_id = "customer123"
    site_id = "Sibaya"
    asset_id = "INV001"

    print("=== COMPLETE WORKFLOW EXAMPLE ===\n")

    # Step 1: Get current forecast
    print("Step 1: Get Solar Forecast")
    forecast = client.forecasting.get_site_forecast(site_id=site_id, forecast_hours=24)
    print(f"  - Site: {forecast['site_id']}")
    print(f"  - Devices: {forecast['device_count']}")
    print(f"  - Next hour forecast: {forecast['forecasts'][0]['kWh_forecast']} kWh")

    # Step 2: Check asset health via detection
    print("\nStep 2: Run Fault Detection")
    detection = client.terminal.run_detection(
        customer_id=customer_id, asset_id=asset_id, lookback_hours=6
    )
    detection_id = detection["detection_id"]
    severity = detection["analysis"]["severity_label"]
    print(f"  - Detection ID: {detection_id}")
    print(f"  - Severity: {severity}")
    print(f"  - Status: {detection['analysis']['status']}")

    # Step 3: If fault detected, run diagnostics
    if severity in ["High", "Medium"]:
        print("\nStep 3: Run Diagnostics (fault detected)")
        diagnostic = client.terminal.run_diagnostics(
            customer_id=customer_id, asset_id=asset_id, detection_id=detection_id
        )
        print(f"  - Root cause: {diagnostic['analysis']['root_cause']}")
        print(f"  - Category: {diagnostic['analysis']['category']}")
        print(f"  - Confidence: {diagnostic['analysis']['confidence']}")

        # Step 4: Query energy analyst for compliance info
        print("\nStep 4: Query Energy Analyst for Compliance")
        try:
            compliance_info = client.energy_analyst.query(
                question=f"What are the maintenance requirements for {diagnostic['analysis']['category']}?",
                n_results=2,
            )
            print(f"  - Answer: {compliance_info['answer'][:200]}...")
        except Exception as e:
            print(f"  - Energy Analyst unavailable: {e}")

        # Step 5: Create maintenance schedule
        print("\nStep 5: Create Maintenance Schedule")
        schedule = client.terminal.create_schedule(
            customer_id=customer_id,
            asset_id=asset_id,
            description=f"Maintenance: {diagnostic['analysis']['root_cause']}",
            priority="High" if severity == "High" else "Medium",
            estimated_duration_hours=8,
        )
        print(f"  - Schedule created: {schedule['schedule_id']}")

    # Step 6: Review activity stream
    print("\nStep 6: Review Recent Activities")
    activities = client.terminal.list_activities(customer_id=customer_id)
    print(f"  - Total activities (24h): {len(activities)}")
    print("  - Recent activities:")
    for activity in activities[:3]:
        print(f"    [{activity['phase']}] {activity['title']}")

    # Step 7: Check ML model registry
    print("\nStep 7: Check ML Model Registry")
    models = client.terminal.get_ml_models()
    print(f"  - Registered models: {len(models)}")
    if models:
        latest_model = models[0]
        print(
            f"  - Latest: {latest_model.get('model_name', 'N/A')} "
            f"(version {latest_model.get('version', 'N/A')})"
        )

    # Step 8: Get nowcast data for monitoring
    print("\nStep 8: Get Nowcast Data")
    nowcast = client.terminal.get_nowcast_data(customer_id=customer_id, time_range="1h")
    metrics = nowcast.get("latest_metrics", {})
    print(f"  - Total power: {metrics.get('total_power_kw', 0)} kW")
    print(f"  - Active inverters: {metrics.get('active_inverters', 0)}")
    print(f"  - Avg temperature: {metrics.get('avg_temperature_c', 0)}°C")

    print("\n=== WORKFLOW COMPLETE ===")


if __name__ == "__main__":
    main()
