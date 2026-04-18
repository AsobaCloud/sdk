"""Example usage of Terminal API client for OODA workflow."""

from ona_platform import OnaClient


def main():
    # Initialize client
    client = OnaClient()
    customer_id = "customer123"
    asset_id = "asset456"

    # OBSERVE: Run fault detection
    print("=== OBSERVE: Fault Detection ===")
    detection = client.terminal.run_detection(
        customer_id=customer_id,
        asset_id=asset_id,
        lookback_hours=6
    )
    detection_id = detection['detection_id']
    print(f"Detection ID: {detection_id}")
    print(f"Severity: {detection['analysis']['severity_label']}")
    print(f"Fault type: {detection['analysis']['fault_type']}")
    print(f"Summary: {detection['analysis']['summary']}")

    # ORIENT: Run AI diagnostics
    print("\n=== ORIENT: AI Diagnostics ===")
    diagnostic = client.terminal.run_diagnostics(
        customer_id=customer_id,
        asset_id=asset_id,
        detection_id=detection_id,
        lookback_hours=6
    )
    print(f"Diagnostic ID: {diagnostic['diagnostic_id']}")
    print(f"Root cause: {diagnostic['analysis']['root_cause']}")
    print(f"Category: {diagnostic['analysis']['category']}")
    print(f"Confidence: {diagnostic['analysis']['confidence']}")
    print("Recommended actions:")
    for action in diagnostic['analysis'].get('recommended_actions', []):
        print(f"  - {action}")

    # DECIDE: Create maintenance schedule
    print("\n=== DECIDE: Maintenance Scheduling ===")
    schedule = client.terminal.create_schedule(
        customer_id=customer_id,
        asset_id=asset_id,
        description=f"Maintenance for {diagnostic['analysis']['root_cause']}",
        priority="High",
        estimated_duration_hours=8
    )
    print(f"Schedule created: {schedule['schedule_id']}")

    # ACT: List activities
    print("\n=== ACT: Activity Stream ===")
    activities = client.terminal.list_activities(customer_id=customer_id)
    print(f"Total activities (last 24h): {len(activities)}")
    for activity in activities[:5]:
        print(f"  [{activity['phase']}] {activity['title']}: {activity['description']}")

    # Asset Management
    print("\n=== Asset Management ===")
    assets = client.terminal.list_assets(customer_id=customer_id)
    print(f"Total assets: {len(assets)}")
    for asset in assets[:3]:
        print(f"  - {asset['name']} ({asset['type']}): {asset['capacity_kw']} kW")

    # ML Integration
    print("\n=== ML Integration ===")
    forecast_results = client.terminal.get_forecast_results(customer_id=customer_id)
    print(f"Forecast results: {len(forecast_results)}")

    ml_ooda = client.terminal.get_ml_ooda_summaries(customer_id=customer_id)
    print(f"ML-enhanced OODA summaries: {len(ml_ooda)}")


if __name__ == '__main__':
    main()
