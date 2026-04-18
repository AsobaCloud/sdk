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
 *   export INVERTER_TELEMETRY_ENDPOINT=https://af5jy5ob3e.execute-api.af-south-1.amazonaws.com/prod
 *   export INVERTER_TELEMETRY_API_KEY=your_api_key
 */

const { OnaSDK, AuthenticationError, ValidationError } = require('../src/index');
const { RateLimitError, ServiceUnavailableError } = require('../src/services/InverterTelemetryClient');

async function main() {
  // Initialize SDK — picks up endpoint and API key from environment variables
  const sdk = new OnaSDK({
    endpoints: {
      inverterTelemetry: process.env.INVERTER_TELEMETRY_ENDPOINT,
    },
    inverterTelemetryApiKey: process.env.INVERTER_TELEMETRY_API_KEY,
  });

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

    dataStart = period.first_record; // e.g. '2025-11-01T02:40:00'
  } catch (err) {
    if (err instanceof AuthenticationError) {
      console.error('Auth error:', err.message);
      return;
    }
    throw err;
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
    records.forEach(r =>
      console.log(`  ${r.timestamp}  power=${r.power} kW  temp=${r.temperature}°C  ` +
                  `state=${r.inverter_state}  error=${r.error_type}`)
    );
  } catch (err) {
    if (err instanceof ValidationError) console.error('Validation error:', err.message);
    else if (err instanceof AuthenticationError) console.error('Auth error:', err.message);
    else throw err;
  }

  // ---------------------------------------------------------------------------
  // Step 3: Query daily resolution data
  // ---------------------------------------------------------------------------
  console.log('\n=== Step 3: Historical Inverter Telemetry (daily) ===');
  try {
    const records = await it.getInverterTelemetry({
      asset_id: assetId,
      site_id: siteId,
      time_range: { start: '2025-11-01T00:00:00', end: '2025-11-30T23:59:59' },
      resolution: 'daily',
      limit: 30,
    });
    console.log(`Retrieved ${records.length} daily records`);
    records.slice(0, 5).forEach(r =>
      console.log(`  ${r.timestamp}  kWh=${r.kWh}  PF=${r.PF}`)
    );
  } catch (err) {
    if (err instanceof AuthenticationError) console.error('Auth error:', err.message);
    else throw err;
  }

  // ---------------------------------------------------------------------------
  // Step 4: Query all inverters at a site
  // ---------------------------------------------------------------------------
  console.log('\n=== Step 4: Site Telemetry (all inverters) ===');
  try {
    const siteData = await it.getSiteTelemetry({
      site_id: siteId,
      time_range: { start: dataStart, end: '2025-11-01T06:00:00' },
      resolution: '5min',
      limit: 20,
    });
    const inverterIds = Object.keys(siteData);
    console.log(`Found ${inverterIds.length} inverters at site`);
    inverterIds.forEach(id => {
      const recs = siteData[id];
      console.log(`  ${id}: ${recs.length} records, ` +
                  `first=${recs[0].timestamp}, last=${recs[recs.length - 1].timestamp}`);
    });
  } catch (err) {
    if (err instanceof AuthenticationError) console.error('Auth error:', err.message);
    else throw err;
  }

  // ---------------------------------------------------------------------------
  // Step 5: Stream live telemetry (stops after 3 records for demo)
  // polling_interval minimum is 5 seconds; use 30s for production
  // ---------------------------------------------------------------------------
  console.log('\n=== Step 5: Live Stream — Single Inverter (stops after 3 records) ===');
  try {
    let count = 0;
    for await (const record of it.streamInverter({
      asset_id: assetId,
      site_id: siteId,
      polling_interval: 30,
    })) {
      console.log(`  [${count + 1}] ${record.timestamp}  power=${record.power} kW  ` +
                  `cursor=${record.cursor.slice(0, 24)}...`);
      count++;
      if (count >= 3) break; // save record.cursor here to resume later
    }
  } catch (err) {
    if (err instanceof AuthenticationError) console.error('Auth error:', err.message);
    else if (err instanceof RateLimitError) console.error('Rate limit exceeded:', err.message);
    else throw err;
  }

  // ---------------------------------------------------------------------------
  // Step 6: Resume a stream from a saved cursor
  // ---------------------------------------------------------------------------
  console.log('\n=== Step 6: Resume Stream from Cursor ===');
  try {
    // Get a cursor from the first record
    let savedCursor = null;
    for await (const record of it.streamInverter({
      asset_id: assetId,
      site_id: siteId,
      polling_interval: 30,
    })) {
      savedCursor = record.cursor;
      console.log(`  Saved cursor: ${savedCursor.slice(0, 30)}...`);
      break;
    }

    if (savedCursor) {
      console.log('  Resuming from cursor — only records after the saved position:');
      let count = 0;
      for await (const record of it.streamInverter({
        asset_id: assetId,
        site_id: siteId,
        cursor: savedCursor,
        polling_interval: 30,
      })) {
        console.log(`  ${record.timestamp}  power=${record.power} kW`);
        count++;
        if (count >= 2) break;
      }
    }
  } catch (err) {
    if (err instanceof AuthenticationError) console.error('Auth error:', err.message);
    else throw err;
  }

  // ---------------------------------------------------------------------------
  // Step 7: Stream all inverters at a site
  // ---------------------------------------------------------------------------
  console.log('\n=== Step 7: Live Stream — All Inverters at Site (stops after 5 records) ===');
  try {
    let count = 0;
    for await (const record of it.streamSite({
      site_id: siteId,
      polling_interval: 30,
    })) {
      console.log(`  [${count + 1}] ${record.asset_id} @ ${record.timestamp}  ` +
                  `power=${record.power} kW`);
      count++;
      if (count >= 5) break;
    }
  } catch (err) {
    if (err instanceof AuthenticationError) console.error('Auth error:', err.message);
    else if (err instanceof RateLimitError) console.error('Rate limit exceeded:', err.message);
    else if (err instanceof ServiceUnavailableError) console.error('Service unavailable:', err.message);
    else throw err;
  }
}

main().catch(console.error);
