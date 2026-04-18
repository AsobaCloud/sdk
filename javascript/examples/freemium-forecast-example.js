#!/usr/bin/env node
/**
 * Freemium Forecast Example
 *
 * Generate a 24-hour solar energy forecast from a CSV file.
 * No API key required.
 *
 * Usage:
 *   node freemium-forecast-example.js
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { OnaSDK } = require('../src/index');

function createSampleCsv(filePath) {
  const rows = [
    'Timestamp,Power (kW)',
    '2025-12-01T00:00:00Z,0',
    '2025-12-01T01:00:00Z,0',
    '2025-12-01T05:00:00Z,10.5',
    '2025-12-01T06:00:00Z,55.2',
    '2025-12-01T07:00:00Z,120.7',
    '2025-12-01T08:00:00Z,380.4',
    '2025-12-01T09:00:00Z,720.1',
    '2025-12-01T10:00:00Z,1100.3',
    '2025-12-01T11:00:00Z,1450.8',
    '2025-12-01T12:00:00Z,1850.2',
    '2025-12-01T13:00:00Z,1780.5',
    '2025-12-01T14:00:00Z,1620.9',
    '2025-12-01T15:00:00Z,1200.4',
    '2025-12-01T16:00:00Z,750.6',
    '2025-12-01T17:00:00Z,320.1',
    '2025-12-01T18:00:00Z,80.3',
    '2025-12-01T19:00:00Z,0',
    '2025-12-01T20:00:00Z,0',
  ];
  fs.writeFileSync(filePath, rows.join('\n'));
}

async function main() {
  const sdk = new OnaSDK();

  // Create a temporary sample CSV
  const csvPath = path.join(os.tmpdir(), `ona-sample-${Date.now()}.csv`);
  createSampleCsv(csvPath);

  console.log('=== Freemium Forecast Example ===');
  console.log(`CSV: ${csvPath}`);
  console.log();

  try {
    const result = await sdk.freemiumForecast.getForecast({
      csvPath,
      email: 'demo@example.com',
      siteName: 'Demo Solar Site',
      location: 'Durban',
    });

    const { forecast } = result;
    console.log(`Site:         ${forecast.site_name}`);
    console.log(`Location:     ${forecast.location}`);
    console.log(`Model type:   ${forecast.model_type}`);
    console.log(`Generated at: ${forecast.generated_at}`);
    console.log();

    const s = forecast.summary || {};
    console.log('=== Summary ===');
    console.log(`  Total 24h:   ${s.total_kwh_24h ?? 'N/A'} kWh`);
    console.log(`  Peak hour:   ${s.peak_hour ?? 'N/A'}`);
    console.log(`  Peak output: ${s.peak_kwh ?? 'N/A'} kWh`);
    console.log();

    console.log('=== Hourly Forecast (first 6 hours) ===');
    forecast.forecasts.slice(0, 6).forEach(p => {
      console.log(`  ${p.timestamp}  ${String(p.kWh_forecast.toFixed(1)).padStart(8)} kWh  confidence=${(p.confidence * 100).toFixed(0)}%`);
    });

  } catch (err) {
    console.error(`Error: ${err.constructor.name}: ${err.message}`);
  } finally {
    fs.unlinkSync(csvPath);
  }
}

main().catch(err => {
  console.error('Unhandled error:', err);
  process.exit(1);
});
