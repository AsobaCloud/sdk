/**
 * Example usage of the Partner API client
 *
 * Prerequisites:
 *   export ASOBA_API_KEY=your_api_key
 */
const { OnaSDK } = require('../src/index');

async function main() {
  // Initialize SDK — picks up ASOBA_API_KEY from environment
  const sdk = new OnaSDK();

  if (!sdk.config.apiKey) {
    console.error('❌ ASOBA_API_KEY environment variable not set');
    process.exit(1);
  }

  if (!sdk.partner) {
    console.error('Partner API client not initialized. Check your configuration.');
    process.exit(1);
  }

  const siteId = 'Sibaya';

  try {
    console.log(`--- Fetching KPI Rollup for ${siteId} ---`);
    const start = Date.now();
    const kpis = await sdk.partner.getKpiRollup({ site_id: siteId });
    const duration = Date.now() - start;
    console.log(`Fetch 1 took ${duration}ms`);
    console.log('Data:', JSON.stringify(kpis, null, 2));

    console.log(`\n--- Fetching KPI Rollup again (should use cache) ---`);
    const start2 = Date.now();
    const cachedKpis = await sdk.partner.getKpiRollup({ site_id: siteId });
    const duration2 = Date.now() - start2;
    console.log(`Fetch 2 took ${duration2}ms (status: ${cachedKpis ? 'OK' : 'Empty'})`);

    if (duration2 < duration) {
      console.log(
        '✅ Success: Second fetch was faster (served from cache via 304 Not Modified)'
      );
    }

    console.log(`\n--- Fetching Maintenance Signals ---`);
    const signals = await sdk.partner.getMaintenanceSignals({
      site_id: siteId,
      severity: 'high',
    });
    console.log('Signals:', JSON.stringify(signals, null, 2));

    console.log(`\n--- Fetching Forecast Snapshot ---`);
    const forecast = await sdk.partner.getForecastSnapshot({ site_id: siteId });
    console.log(
      `Horizon: ${forecast.horizon_hours}h, intervals: ${(forecast.intervals || []).length}`
    );

    console.log(`\n--- Fetching Maintenance Schedule (SEP-062) ---`);
    const schedule = await sdk.partner.getMaintenanceSchedule({ site_id: siteId });
    const summary = schedule.summary || {};
    console.log('Horizon:', JSON.stringify(schedule.horizon));
    console.log('Total tasks:', summary.total_tasks);
    console.log('By priority:', JSON.stringify(summary.by_priority));
    const tasks = schedule.tasks || [];
    if (tasks.length > 0) {
      console.log('First task:', JSON.stringify(tasks[0], null, 2));
    } else {
      console.log('No scheduled maintenance tasks yet (insufficient anomaly history).');
    }
  } catch (error) {
    console.error('Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
  }
}

main();
