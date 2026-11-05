/**
 * Behavioral tests for JS SDK edge transport mode (Issue #1).
 *
 * Verifies that OnaSDK in edge mode sends plain HTTP (no AWS signing)
 * and reads edge endpoints from environment variables.
 */

'use strict';

const assert = require('assert');
const http = require('http');

// ---------------------------------------------------------------------------
// JS-EDGE-1: Edge mode skips AWS Sig v4 signing
// ---------------------------------------------------------------------------

async function test_edge_forecasting_no_signing() {
  let receivedHeaders = {};
  let receivedBody = {};

  const server = http.createServer((req, res) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      receivedHeaders = req.headers;
      try { receivedBody = JSON.parse(body || '{}'); } catch (_) {}
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ forecasts: [{ kWh_forecast: 5.2 }] }));
    });
  });

  await new Promise(resolve => server.listen(8299, '127.0.0.1', resolve));

  try {
    const { OnaSDK } = require('../src/index.js');

    const sdk = new OnaSDK({
      mode: 'edge',
      apiKey: 'edge-test-key',
      endpoints: { forecasting: 'http://127.0.0.1:8299' },
    });

    const result = await sdk.forecasting.getSiteForecast({ site_id: 'Sibaya', forecast_hours: 24 });

    // In edge mode, no AWS auth headers should be present
    assert(
      !receivedHeaders['authorization'],
      'Authorization header must NOT be present in edge mode'
    );
    assert(
      !receivedHeaders['x-amz-date'],
      'X-Amz-Date header must NOT be present in edge mode'
    );
    assert.strictEqual(receivedBody.site_id, 'Sibaya', 'site_id must be Sibaya');
    assert.strictEqual(receivedBody.forecast_hours, 24, 'forecast_hours must be 24');
    assert.strictEqual(result.forecasts[0].kWh_forecast, 5.2, 'kWh_forecast must be 5.2');

    console.log('test_edge_forecasting_no_signing: PASSED');
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}

// ---------------------------------------------------------------------------
// JS-EDGE-2: Config reads edge mode + endpoints from environment
// ---------------------------------------------------------------------------

function test_edge_config_from_env() {
  const prev = {
    ONA_MODE: process.env.ONA_MODE,
    FORECAST_API_URL: process.env.FORECAST_API_URL,
    TERMINAL_API_URL: process.env.TERMINAL_API_URL,
  };

  process.env.ONA_MODE = 'edge';
  process.env.FORECAST_API_URL = 'http://localhost:8002';
  process.env.TERMINAL_API_URL = 'http://localhost:8001';

  // Force re-require to pick up new env
  delete require.cache[require.resolve('../src/config.js')];
  const Config = require('../src/config.js');
  const config = new Config();

  assert.strictEqual(config.mode, 'edge', 'mode must be "edge"');
  assert.strictEqual(
    config.endpoints.forecasting,
    'http://localhost:8002',
    'forecasting endpoint must be http://localhost:8002'
  );
  assert.strictEqual(
    config.endpoints.terminal,
    'http://localhost:8001',
    'terminal endpoint must be http://localhost:8001'
  );
  assert.strictEqual(config.isEdge(), true, 'isEdge() must return true');

  // Restore
  for (const [k, v] of Object.entries(prev)) {
    if (v === undefined) { delete process.env[k]; } else { process.env[k] = v; }
  }
  delete require.cache[require.resolve('../src/config.js')];

  console.log('test_edge_config_from_env: PASSED');
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------

(async () => {
  try {
    await test_edge_forecasting_no_signing();
    test_edge_config_from_env();
    console.log('\nAll JS edge transport tests PASSED');
  } catch (err) {
    console.error('\nTest FAILED:', err.message);
    process.exit(1);
  }
})();
