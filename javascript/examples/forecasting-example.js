/**
 * Forecasting API Example
 * Demonstrates energy forecasting at different levels
 */

const { OnaSDK } = require('../src/index');

async function main() {
  const sdk = new OnaSDK({
    region: 'af-south-1',
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
    },
    endpoints: {
      forecasting: process.env.ONA_FORECASTING_ENDPOINT || 'https://forecasting.api.asoba.co'
    }
  });

  try {
    // Device-level forecast
    console.log('--- Device-Level Forecast ---');
    const deviceForecast = await sdk.forecasting.getDeviceForecast({
      site_id: 'Sibaya',
      device_id: 'INV001',
      forecast_hours: 24
    });

    console.log(`Device: ${deviceForecast.device_id} at site ${deviceForecast.site_id}`);
    console.log(`Model type: ${deviceForecast.model_info.model_type}`);
    console.log(`Generated at: ${deviceForecast.generated_at}`);
    console.log(`\nFirst 5 forecast points:`);

    deviceForecast.forecasts.slice(0, 5).forEach(point => {
      console.log(`  ${point.timestamp}: ${point.kWh_forecast?.toFixed(2)} kWh (${point.hour_ahead}h ahead)`);
    });

    // Site-level forecast (aggregated)
    console.log('\n--- Site-Level Forecast (Aggregated) ---');
    const siteForecast = await sdk.forecasting.getSiteForecast({
      site_id: 'Sibaya',
      forecast_hours: 48,
      include_device_breakdown: true
    });

    console.log(`Site: ${siteForecast.site_id}`);
    console.log(`Devices included: ${siteForecast.device_count}`);
    console.log(`Aggregation method: ${siteForecast.model_info.aggregation_method}`);
    console.log(`\nAggregated forecast (first 5 hours):`);

    siteForecast.forecasts.slice(0, 5).forEach(point => {
      console.log(`  ${point.timestamp}: ${point.kWh_forecast?.toFixed(2)} kWh (${point.hour_ahead}h ahead)`);
    });

    if (siteForecast.device_forecasts) {
      console.log(`\nDevice breakdown available for ${siteForecast.device_forecasts.length} devices`);
    }

    // Calculate peak forecast
    const peakForecast = siteForecast.forecasts.reduce((max, point) => {
      return (point.kWh_forecast || 0) > (max.kWh_forecast || 0) ? point : max;
    });

    console.log(`\nPeak forecast: ${peakForecast.kWh_forecast?.toFixed(2)} kWh at ${peakForecast.timestamp}`);

    // Customer-level forecast (legacy)
    console.log('\n--- Customer-Level Forecast (Legacy) ---');
    const customerForecast = await sdk.forecasting.getCustomerForecast({
      customer_id: 'customer123',
      forecast_hours: 24
    });

    console.log(`Customer: ${customerForecast.customer_id}`);
    console.log(`Model type: ${customerForecast.model_info.model_type}`);

    if (customerForecast.model_info.customer_validation_loss) {
      console.log(`Validation loss: ${customerForecast.model_info.customer_validation_loss}`);
    }

    // Calculate total energy forecast
    const totalEnergy = customerForecast.forecasts.reduce((sum, point) => {
      return sum + (point.kWh_forecast || 0);
    }, 0);

    console.log(`\nTotal forecasted energy (24h): ${totalEnergy.toFixed(2)} kWh`);
    console.log(`Average hourly generation: ${(totalEnergy / 24).toFixed(2)} kWh`);

  } catch (error) {
    console.error('Error:', error.message);
    if (error.code) {
      console.error('Error code:', error.code);
    }
    if (error.statusCode) {
      console.error('HTTP status:', error.statusCode);
    }
  }
}

main().catch(console.error);
