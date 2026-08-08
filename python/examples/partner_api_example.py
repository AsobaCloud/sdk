import json
import time

from asoba import OnaClient


def main():
    # Initialize client — picks up ASOBA_API_KEY from environment
    client = OnaClient()

    if not client.config.api_key:
        print("❌ ASOBA_API_KEY environment variable not set")
        return

    site_id = "Sibaya"

    try:
        print(f"--- Fetching KPI Rollup for {site_id} ---")
        start = time.time()
        kpis = client.partner.get_kpi_rollup(site_id=site_id)
        duration = (time.time() - start) * 1000
        print(f"Fetch 1 took {duration:.2f}ms")
        print("Data:", json.dumps(kpis, indent=2, default=str))

        print("\n--- Fetching KPI Rollup again (should use cache) ---")
        start2 = time.time()
        cached_kpis = client.partner.get_kpi_rollup(site_id=site_id)
        duration2 = (time.time() - start2) * 1000
        print(f"Fetch 2 took {duration2:.2f}ms (status: {'OK' if cached_kpis else 'Empty'})")

        if duration2 < duration:
            print("✅ Success: Second fetch was faster (served from cache via 304 Not Modified)")

        print("\n--- Fetching Maintenance Signals ---")
        signals = client.partner.get_maintenance_signals(
            site_id=site_id,
            severity="high",
        )
        print("Signals:", json.dumps(signals, indent=2, default=str))

        print("\n--- Fetching Forecast Snapshot ---")
        forecast = client.partner.get_forecast_snapshot(site_id=site_id)
        print(
            f"Horizon: {forecast.get('horizon_hours')}h, "
            f"intervals: {len(forecast.get('intervals', []))}"
        )

        print("\n--- Fetching Maintenance Schedule (SEP-062) ---")
        schedule = client.partner.get_maintenance_schedule(site_id=site_id)
        summary = schedule.get("summary", {})
        print(f"Horizon: {schedule.get('horizon')}")
        print(f"Total tasks: {summary.get('total_tasks')}")
        print(f"By priority: {summary.get('by_priority')}")
        tasks = schedule.get("tasks", [])
        if tasks:
            print(f"First task: {json.dumps(tasks[0], indent=2, default=str)}")
        else:
            print("No scheduled maintenance tasks yet (insufficient anomaly history).")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
