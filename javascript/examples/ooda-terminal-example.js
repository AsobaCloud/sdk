#!/usr/bin/env node
/**
 * OODA Terminal API Example
 *
 * This example demonstrates how to use the OODA Terminal API to query and stream
 * OODA (Observe, Orient, Decide, Act) alerts from terminal devices.
 *
 * Requirements:
 * - Set ASOBA_API_KEY environment variable
 *
 * Example usage:
 *   export ASOBA_API_KEY="your-api-key-here"
 *   node ooda-terminal-example.js
 */

const { OnaSDK } = require('../src/index');

async function main() {
  console.log('🔗 OODA Terminal API Example');

  // Initialize the SDK — picks up ASOBA_API_KEY from environment
  const sdk = new OnaSDK();

  if (!sdk.config.apiKey) {
    console.log('❌ ASOBA_API_KEY environment variable not set');
    console.log('   Set it to your Asoba API key');
    return;
  }

  console.log(`   Endpoint: ${sdk.config.endpoints.oodaTerminal}`);
  console.log();

  // Example site and terminal device
  const siteId = 'Sibaya';
  const terminalDeviceId = 'TERM-1000000054495190';

  try {
    // 1. Discover available data period
    console.log('📊 Discovering available data period...');
    const dataPeriod = await sdk.oodaTerminal.getDataPeriod({ site_id: siteId });
    console.log(`   Site: ${dataPeriod.site_id}`);
    console.log(`   First record: ${dataPeriod.first_record}`);
    console.log(`   Last record: ${dataPeriod.last_record}`);
    console.log();

    // 2. Query terminal alerts for the last 24 hours
    console.log('🔍 Querying terminal alerts (last 24 hours)...');
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000);
    const timeRange = { start: startTime.toISOString(), end: endTime.toISOString() };

    const alerts = await sdk.oodaTerminal.getTerminalAlerts({
      terminal_device_id: terminalDeviceId,
      site_id: siteId,
      time_range: timeRange,
      resolution: '5min',
      limit: 10,
    });
    console.log(`   Found ${alerts.length} alerts`);
    alerts.slice(0, 3).forEach((alert) => {
      console.log(`   ${alert.timestamp}: ${alert.alert_severity.toUpperCase()} - ${alert.message}`);
    });
    console.log();

    // 3. Query site alerts (all terminal devices)
    console.log('🔍 Querying site alerts...');
    const siteAlerts = await sdk.oodaTerminal.getSiteAlerts({
      site_id: siteId,
      time_range: timeRange,
      resolution: '5min',
      limit: 5,
    });
    const totalAlerts = Object.values(siteAlerts).reduce((sum, a) => sum + a.length, 0);
    console.log(`   Found ${totalAlerts} alerts across ${Object.keys(siteAlerts).length} devices`);
    console.log();

    // 4. Stream live terminal alerts (one poll)
    console.log('📡 Streaming live terminal alerts (one poll)...');
    for await (const alert of sdk.oodaTerminal.streamTerminal({
      terminal_device_id: terminalDeviceId,
      site_id: siteId,
      polling_interval: 5,
    })) {
      console.log(`   ${alert.timestamp}: ${alert.alert_severity.toUpperCase()} - ${alert.message}`);
      break;
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

main().catch((err) => {
  console.error('Unhandled error:', err);
  process.exit(1);
});
