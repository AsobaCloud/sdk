"""
Inverter Telemetry Example
Demonstrates the correct workflow for querying historical and streaming
live inverter telemetry data.

The correct workflow is:
  1. Call get_data_period() to discover what time range has data
  2. Use those timestamps in your historical queries
  3. Stream live data using stream_inverter() or stream_site()

Prerequisites:
    export ASOBA_API_KEY=your_api_key
"""

from asoba import OnaClient
from asoba.exceptions import AuthenticationError, ValidationError
from asoba.models.telemetry import TimeRange
from asoba.services.inverter_telemetry import RateLimitError


def main():
    # Initialize client — picks up ASOBA_API_KEY from environment
    client = OnaClient()
    it = client.inverter_telemetry

    site_id = "Sibaya"
    asset_id = "INV-1000000054495190"

    # -------------------------------------------------------------------------
    # Step 1: Always discover the available data period first.
    # Querying a time range with no data returns [] silently — knowing the
    # available range upfront avoids wasted calls.
    # -------------------------------------------------------------------------
    print("=== Step 1: Discover available data period ===")
    try:
        period = it.get_data_period(site_id=site_id)
        print("Site data period:")
        print(f"  first_record: {period['first_record']}")
        print(f"  last_record:  {period['last_record']}")

        # Also check a specific inverter
        inv_period = it.get_data_period(site_id=site_id, asset_id=asset_id)
        print(f"Inverter {asset_id}:")
        print(f"  first_record: {inv_period['first_record']}")
        print(f"  last_record:  {inv_period['last_record']}")
    except AuthenticationError as e:
        print(f"Auth error: {e}")
        return

    # Use the discovered start time for subsequent queries
    data_start = period["first_record"]  # e.g. '2025-11-01T02:40:00'

    # -------------------------------------------------------------------------
    # Step 2: Query historical 5-minute data using the discovered range
    # -------------------------------------------------------------------------
    print("\n=== Step 2: Historical Inverter Telemetry (5-min) ===")
    try:
        records = it.get_inverter_telemetry(
            asset_id=asset_id,
            site_id=site_id,
            time_range=TimeRange(
                start=data_start,
                end="2025-11-01T06:00:00",
            ),
            resolution="5min",
            limit=10,
        )
        print(f"Retrieved {len(records)} records")
        for r in records:
            print(
                f"  {r.timestamp}  power={r.power} kW  temp={r.temperature}°C  "
                f"state={r.inverter_state}  error={r.error_type}"
            )
    except ValidationError as e:
        print(f"Validation error: {e}")
    except AuthenticationError as e:
        print(f"Auth error: {e}")

    # -------------------------------------------------------------------------
    # Step 3: Query daily resolution
    # -------------------------------------------------------------------------
    print("\n=== Step 3: Historical Inverter Telemetry (daily) ===")
    try:
        daily = it.get_inverter_telemetry(
            asset_id=asset_id,
            site_id=site_id,
            time_range=TimeRange(start="2025-11-01T00:00:00", end="2025-11-30T23:59:59"),
            resolution="daily",
            limit=30,
        )
        print(f"Retrieved {len(daily)} daily records")
        for r in daily[:5]:
            print(f"  {r.timestamp}  kWh={r.kWh}  PF={r.PF}")
    except ValidationError as e:
        print(f"Validation error: {e}")

    # -------------------------------------------------------------------------
    # Step 4: Query all inverters at a site
    # -------------------------------------------------------------------------
    print("\n=== Step 4: Site Telemetry ===")
    try:
        site_data = it.get_site_telemetry(
            site_id=site_id,
            time_range=TimeRange(start=data_start, end="2025-11-01T06:00:00"),
            resolution="5min",
            limit=20,
        )
        for inv_id, recs in site_data.items():
            print(f"  {inv_id}: {len(recs)} records")
    except ValidationError as e:
        print(f"Validation error: {e}")

    # -------------------------------------------------------------------------
    # Step 5: Stream live data (one poll cycle)
    # -------------------------------------------------------------------------
    print("\n=== Step 5: Stream live inverter data ===")
    try:
        for record in it.stream_inverter(
            asset_id=asset_id,
            site_id=site_id,
            polling_interval=30,
        ):
            print(
                f"  {record.timestamp}  power={record.power} kW  "
                f"cursor={record.cursor[:24]}..."
            )
            break  # remove break for continuous streaming
    except RateLimitError as e:
        print(f"Rate limit: {e}")
    except AuthenticationError as e:
        print(f"Auth error: {e}")


if __name__ == "__main__":
    main()
