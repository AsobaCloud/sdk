import json
import os
import time

from ona_platform import OnaClient


def main():
    # 1. Initialize client
    client = OnaClient(
        partner_api_endpoint=os.getenv("PARTNER_API_ENDPOINT", "https://mock.api.asoba.org"),
        partner_api_key=os.getenv("PARTNER_API_KEY", "mock-key")
    )

    site_id = "Sibaya"

    try:
        print(f"--- Fetching KPI Rollup for {site_id} ---")
        start = time.time()
        kpis = client.partner_api.get_kpi_rollup(site_id=site_id)
        duration = (time.time() - start) * 1000
        print(f"Fetch 1 took {duration:.2f}ms")
        print("Data:", json.dumps(kpis, indent=2))

        print("\n--- Fetching KPI Rollup again (should use cache) ---")
        start2 = time.time()
        cached_kpis = client.partner_api.get_kpi_rollup(site_id=site_id)
        duration2 = (time.time() - start2) * 1000
        print(f"Fetch 2 took {duration2:.2f}ms (status: {'OK' if cached_kpis else 'Empty'})")

        if duration2 < duration:
            print("✅ Success: Second fetch was faster (served from cache via 304 Not Modified)")

        print("\n--- Fetching Maintenance Signals ---")
        signals = client.partner_api.get_maintenance_signals(
            site_id=site_id,
            severity="high"
        )
        print("Signals:", json.dumps(signals, indent=2))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
