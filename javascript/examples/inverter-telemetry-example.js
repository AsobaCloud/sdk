/**
 * Inverter Telemetry Example
 * Demonstrates the correct workflow for querying historical and streaming
 * live inverter telemetry data.
 *
 * The correct workflow is:
 *   1. Call getDataPeriod() to discover what time range has data
 *   2. Use those timestamps in your historical queries
 *   3. Stream live data using streamInverter() or streamSite()
 *
 * Prerequisites:
 *   export ASOBA_API_KEY=your_api_key
 */

const { OnaSDK, AuthenticationError, ValidationError } = require('../src/index');
const { RateLimitError } = require('../src/services/InverterTelemetryClient');

async function main() {
  // Initialize SDK — picks up ASOBA_API_KEY from environment
  const sdk = new OnaSDK();

  const it = sdk.inverterTelemetry;
  const siteId = 'Sibaya';
  const assetId = 'INV-1000000054495190';

  // ---------------------------------------------------------------------------
  // Step 1: Always discover the available data period first.
  // Querying a time range with no data returns [] silently — knowing the
  // available range upfront avoids wasted calls.
  // ---------------------------------------------------------------------------
  console.log('=== Step 1: Discover available data period ===');
  let dataStart;
  try {
    const period = await it.getDataPeriod({ site_id: siteId });
    console.log('Site data period:');
    console.log(`  first_record: ${period.first_record}`);
    console.log(`  last_record:  ${period.last_record}`);

    // Also check a specific inverter
    const invPeriod = await it.getDataPeriod({ site_id: siteId, asset_id: assetId });
    console.log(`Inverter ${assetId}:`);
    console.log(`  first_record: ${invPeriod.first_record}`);
    console.log(`  last_record:  ${invPeriod.last_record}`);

    dataStart = period.first_record;
  } catch (error) {
    if (error instanceof AuthenticationError) {
      console.error('Auth error:', error.message);
      console.error('Set ASOBA_API_KEY and retry.');
      return;
    }
    throw error;
  }

  // ---------------------------------------------------------------------------
  // Step 2: Query historical 5-minute data using the discovered range
  // ---------------------------------------------------------------------------
  console.log('\n=== Step 2: Historical Inverter Telemetry (5-min) ===');
  try {
    const records = await it.getInverterTelemetry({
      asset_id: assetId,
      site_id: siteId,
      time_range: { start: dataStart, end: '2025-11-01T06:00:00' },
      resolution: '5min',
      limit: 10,
    });
    console.log(`Retrieved ${records.length} records`);
    records.forEach((r) => {
      console.log(
        `  ${r.timestamp}  power=${r.power} kW  temp=${r.temperature}°C  ` +
          `state=${r.inverter_state}  error=${r.error_type}`
      );
    });
  } catch (error) {
    if (error instanceof ValidationError || error instanceof AuthenticationError) {
      console.error(`${error.name}:`, error.message);
    } else {
      throw error;
    }
  }

  // ---------------------------------------------------------------------------
  // Step 3: Stream live data (one poll cycle)
  // ---------------------------------------------------------------------------
  console.log('\n=== Step 3: Stream live inverter data ===');
  try {
    for await (const record of it.streamInverter({
      asset_id: assetId,
      site_id: siteId,
      polling_interval: 30,
    })) {
      console.log(
        `  ${record.timestamp}  power=${record.power} kW  ` +
          `cursor=${String(record.cursor).slice(0, 24)}...`
      );
      break; // remove break for continuous streaming
    }
  } catch (error) {
    if (error instanceof RateLimitError || error instanceof AuthenticationError) {
      console.error(`${error.name}:`, error.message);
    } else {
      throw error;
    }
  }
}

main().catch((err) => {
  console.error('Unhandled error:', err);
  process.exit(1);
});
