/**
 * Example usage of the Partner API client
 */
const { OnaSDK } = require('../src/index');

async function main() {
  // 1. Initialize SDK
  const sdk = new OnaSDK({
    endpoints: {
      partnerApi: process.env.PARTNER_API_ENDPOINT || 'https://mock.api.asoba.org',
    },
    partnerApiKey: process.env.PARTNER_API_KEY || 'mock-key',
  });

  if (!sdk.partnerApi) {
    console.error('Partner API client not initialized. Check your configuration.');
    process.exit(1);
  }

  const siteId = 'Sibaya';

  try {
    console.log(`--- Fetching KPI Rollup for ${siteId} ---`);
    const start = Date.now();
    const kpis = await sdk.partnerApi.getKpiRollup({ site_id: siteId });
    const duration = Date.now() - start;
    console.log(`Fetch 1 took ${duration}ms`);
    console.log('Data:', JSON.stringify(kpis, null, 2));

    console.log(`\n--- Fetching KPI Rollup again (should use cache) ---`);
    const start2 = Date.now();
    const cachedKpis = await sdk.partnerApi.getKpiRollup({ site_id: siteId });
    const duration2 = Date.now() - start2;
    console.log(`Fetch 2 took ${duration2}ms (status: ${cachedKpis ? 'OK' : 'Empty'})`);

    if (duration2 < duration) {
      console.log(
        '✅ Success: Second fetch was faster (served from cache via 304 Not Modified)'
      );
    }

    console.log(`\n--- Fetching Maintenance Signals ---`);
    const signals = await sdk.partnerApi.getMaintenanceSignals({
      site_id: siteId,
      severity: 'high',
    });
    console.log('Signals:', JSON.stringify(signals, null, 2));

  } catch (error) {
    console.error('Error:', error.message);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
  }
}

main();
