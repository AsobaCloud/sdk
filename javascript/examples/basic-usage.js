/**
 * Basic Usage Example
 * Demonstrates SDK initialization and basic operations
 */

const { OnaSDK } = require('../src/index');

async function main() {
  // Initialize the SDK
  const sdk = new OnaSDK({
    region: 'af-south-1',
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
    },
    endpoints: {
      forecasting: process.env.ONA_FORECASTING_ENDPOINT || 'https://forecasting.api.asoba.co',
      terminal: process.env.ONA_TERMINAL_ENDPOINT || 'https://terminal.api.asoba.co',
      edgeRegistry: process.env.ONA_EDGE_REGISTRY_ENDPOINT || 'http://edge-registry:8082',
      energyAnalyst: process.env.ONA_ENERGY_ANALYST_ENDPOINT || 'http://energy-analyst:8000'
    }
  });

  console.log('✓ SDK initialized successfully');
  console.log(`SDK Version: ${OnaSDK.getVersion()}`);

  try {
    // Example 1: Get site forecast
    console.log('\n--- Example 1: Site Forecast ---');
    const forecast = await sdk.forecasting.getSiteForecast({
      site_id: 'Sibaya',
      forecast_hours: 24
    });
    console.log(`Forecast generated at: ${forecast.generated_at}`);
    console.log(`Number of forecast hours: ${forecast.forecast_hours}`);
    console.log(`First forecast point: ${JSON.stringify(forecast.forecasts[0], null, 2)}`);

    // Example 2: List assets
    console.log('\n--- Example 2: List Assets ---');
    const assetsResult = await sdk.terminal.listAssets({
      customer_id: 'customer123'
    });
    console.log(`Found ${assetsResult.assets.length} assets`);
    if (assetsResult.assets.length > 0) {
      console.log(`First asset: ${assetsResult.assets[0].name} (${assetsResult.assets[0].asset_id})`);
    }

    // Example 3: Query Energy Analyst
    console.log('\n--- Example 3: Energy Analyst Query ---');
    const answer = await sdk.energyAnalyst.query({
      question: 'What are the benefits of solar energy?',
      n_results: 3
    });
    console.log(`Answer: ${answer.answer.substring(0, 200)}...`);
    console.log(`Citation: ${answer.citation}`);

    // Example 4: Get edge devices
    console.log('\n--- Example 4: Edge Devices ---');
    const devices = await sdk.edgeRegistry.getDevices();
    console.log(`Found ${devices.length} edge devices`);
    if (devices.length > 0) {
      console.log(`First device: ${devices[0].name} (${devices[0].status})`);
    }

  } catch (error) {
    console.error('Error:', error.message);
    if (error.statusCode) {
      console.error('Status Code:', error.statusCode);
    }
  }
}

// Run the example
main().catch(console.error);
