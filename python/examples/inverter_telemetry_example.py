"""
Inverter Telemetry Example
Demonstrates the correct workflow for querying historical and streaming
live inverter telemetry data.

The correct workflow is:
  1. Call get_data_period() to discover what time range has data
  2. Use those timestamps in your historical queries
  3. Stream live data using stream_inverter() or stream_site()

Prerequisites:
    export INVERTER_TELEMETRY_ENDPOINT=https://af5jy5ob3e.execute-api.af-south-1.amazonaws.com/prod
    export INVERTER_TELEMETRY_API_KEY=your_api_key
"""

from ona_platform import OnaClient
from ona_platform.models.telemetry import TimeRange
from ona_platform.services.inverter_telemetry import RateLimitError
from ona_platform.exceptions import AuthenticationError, ValidationError


def main():
    # Initialize client — picks up endpoint and API key from environment variables
    client = OnaClient()
    it = client.inverter_telemetry

    site_id = 'Sibaya'
    asset_id = 'INV-1000000054495190'

    # -------------------------------------------------------------------------
    # Step 1: Always discover the available data period first.
    # Querying a time range with no data returns [] silently — knowing the
    # available range upfront avoids wasted calls.
    # -------------------------------------------------------------------------
    print('=== Step 1: Discover available data period ===')
    try:
        period = it.get_data_period(site_id=site_id)
        print(f'Site data period:')
        print(f'  first_record: {period["first_record"]}')
        print(f'  last_record:  {period["last_record"]}')

        # Also check a specific inverter
        inv_period = it.get_data_period(site_id=site_id, asset_id=asset_id)
        print(f'Inverter {asset_id}:')
        print(f'  first_record: {inv_period["first_record"]}')
        print(f'  last_record:  {inv_period["last_record"]}')
    except AuthenticationError as e:
        print(f'Auth error: {e}')
        return

    # Use the discovered start time for subsequent queries
    data_start = period['first_record']  # e.g. '2025-11-01T02:40:00'

    # -------------------------------------------------------------------------
    # Step 2: Query historical 5-minute data using the discovered range
    # -------------------------------------------------------------------------
    print('\n=== Step 2: Historical Inverter Telemetry (5-min) ===')
    try:
        records = it.get_inverter_telemetry(
            asset_id=asset_id,
            site_id=site_id,
            time_range=TimeRange(
                start=data_start,
                end='2025-11-01T06:00:00',
            ),
            resolution='5min',
            limit=10,
        )
        print(f'Retrieved {len(records)} records')
        for r in records:
            print(f'  {r.timestamp}  power={r.power} kW  temp={r.temperature}°C  '
                  f'state={r.inverter_state}  error={r.error_type}')
    except ValidationError as e:
        print(f'Validation error: {e}')
    except AuthenticationError as e:
        print(f'Auth error: {e}')

    # -------------------------------------------------------------------------
    # Step 3: Query daily resolution data
    # -------------------------------------------------------------------------
    print('\n=== Step 3: Historical Inverter Telemetry (daily) ===')
    try:
        records = it.get_inverter_telemetry(
            asset_id=asset_id,
            site_id=site_id,
            time_range=TimeRange(
                start='2025-11-01T00:00:00',
                end='2025-11-30T23:59:59',
            ),
            resolution='daily',
            limit=30,
        )
        print(f'Retrieved {len(records)} daily records')
        for r in records[:5]:
            print(f'  {r.timestamp}  kWh={r.kWh}  PF={r.PF}')
    except AuthenticationError as e:
        print(f'Auth error: {e}')

    # -------------------------------------------------------------------------
    # Step 4: Query all inverters at a site
    # -------------------------------------------------------------------------
    print('\n=== Step 4: Site Telemetry (all inverters) ===')
    try:
        site_data = it.get_site_telemetry(
            site_id=site_id,
            time_range=TimeRange(
                start=data_start,
                end='2025-11-01T06:00:00',
            ),
            resolution='5min',
            limit=20,
        )
        print(f'Found {len(site_data)} inverters at site')
        for inv_id, recs in site_data.items():
            print(f'  {inv_id}: {len(recs)} records, '
                  f'first={recs[0].timestamp}, last={recs[-1].timestamp}')
    except AuthenticationError as e:
        print(f'Auth error: {e}')

    # -------------------------------------------------------------------------
    # Step 5: Stream live telemetry (stops after 3 records for demo)
    # polling_interval minimum is 5 seconds; use 30s for production
    # -------------------------------------------------------------------------
    print('\n=== Step 5: Live Stream — Single Inverter (stops after 3 records) ===')
    try:
        count = 0
        for record in it.stream_inverter(
            asset_id=asset_id,
            site_id=site_id,
            polling_interval=30,
        ):
            print(f'  [{count + 1}] {record.timestamp}  power={record.power} kW  '
                  f'cursor={record.cursor[:24]}...')
            count += 1
            if count >= 3:
                break  # save record.cursor here to resume later
    except AuthenticationError as e:
        print(f'Auth error: {e}')
    except RateLimitError as e:
        print(f'Rate limit exceeded: {e}')

    # -------------------------------------------------------------------------
    # Step 6: Resume a stream from a saved cursor
    # -------------------------------------------------------------------------
    print('\n=== Step 6: Resume Stream from Cursor ===')
    try:
        # Get a cursor from the first record
        saved_cursor = None
        for record in it.stream_inverter(
            asset_id=asset_id,
            site_id=site_id,
            polling_interval=30,
        ):
            saved_cursor = record.cursor
            print(f'  Saved cursor: {saved_cursor[:30]}...')
            break

        if saved_cursor:
            print('  Resuming from cursor — only records after the saved position:')
            count = 0
            for record in it.stream_inverter(
                asset_id=asset_id,
                site_id=site_id,
                cursor=saved_cursor,
                polling_interval=30,
            ):
                print(f'  {record.timestamp}  power={record.power} kW')
                count += 1
                if count >= 2:
                    break
    except AuthenticationError as e:
        print(f'Auth error: {e}')

    # -------------------------------------------------------------------------
    # Step 7: Stream all inverters at a site
    # -------------------------------------------------------------------------
    print('\n=== Step 7: Live Stream — All Inverters at Site (stops after 5 records) ===')
    try:
        count = 0
        for record in it.stream_site(
            site_id=site_id,
            polling_interval=30,
        ):
            print(f'  [{count + 1}] {record.asset_id} @ {record.timestamp}  '
                  f'power={record.power} kW')
            count += 1
            if count >= 5:
                break
    except AuthenticationError as e:
        print(f'Auth error: {e}')
    except RateLimitError as e:
        print(f'Rate limit exceeded: {e}')


if __name__ == '__main__':
    main()
