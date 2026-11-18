/**
 * Behavioral tests for Issue #2: Model Observatory & PVInsight Client Support in JS SDK.
 */

'use strict';

const assert = require('assert');
const http = require('http');

async function test_js_get_model_observatory() {
  let receivedPath = '';
  let receivedBody = {};
  let receivedHeaders = {};

  const server = http.createServer((req, res) => {
    receivedPath = req.url;
    receivedHeaders = req.headers;
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try { receivedBody = JSON.parse(body || '{}'); } catch (_) {}
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: true,
        customer_id: receivedBody.customer_id,
        production_model_id: 'lstm_sibaya_prod',
        challengers: [{ model_id: 'lstm_sibaya_prod', is_production: true, r2: 0.89 }],
      }));
    });
  });

  await new Promise(resolve => server.listen(8391, '127.0.0.1', resolve));

  try {
    const { OnaSDK } = require('../src/index.js');
    const sdk = new OnaSDK({
      mode: 'edge',
      apiKey: 'edge-test-key',
      endpoints: { terminal: 'http://127.0.0.1:8391' },
    });

    assert(
      typeof sdk.terminal.getModelObservatory === 'function',
      'sdk.terminal.getModelObservatory must be a function'
    );

    const result = await sdk.terminal.getModelObservatory({
      customer_id: 'Sibaya',
      site: 'Sibaya-East',
    });

    assert.strictEqual(receivedPath, '/model-observatory');
    assert.strictEqual(receivedBody.customer_id, 'Sibaya');
    assert.strictEqual(receivedBody.site, 'Sibaya-East');
    assert.strictEqual(result.production_model_id, 'lstm_sibaya_prod');
    console.log('test_js_get_model_observatory: PASSED');
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}

async function test_js_pv_insight_client() {
  let receivedPath = '';
  let receivedBody = {};
  let receivedMethod = '';

  const server = http.createServer((req, res) => {
    receivedPath = req.url;
    receivedMethod = req.method;
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try { receivedBody = JSON.parse(body || '{}'); } catch (_) {}
      res.writeHead(200, { 'Content-Type': 'application/json' });
      if (req.url === '/health') {
        res.end(JSON.stringify({ status: 'healthy', service: 'pvInsightService' }));
      } else {
        res.end(JSON.stringify({
          detection: receivedBody.detection,
          llm_analysis: { status: 'completed', recommendation: 'Check inverter MPPT' },
        }));
      }
    });
  });

  await new Promise(resolve => server.listen(8392, '127.0.0.1', resolve));

  try {
    const { OnaSDK } = require('../src/index.js');
    const sdk = new OnaSDK({
      mode: 'edge',
      apiKey: 'edge-test-key',
      endpoints: { pvinsight: 'http://127.0.0.1:8392' },
    });

    assert(sdk.pvInsight, 'sdk.pvInsight must be defined');

    // Health
    const health = await sdk.pvInsight.health();
    assert.strictEqual(health.status, 'healthy');
    assert.strictEqual(receivedPath, '/health');
    assert.strictEqual(receivedMethod, 'GET');

    // Analyze
    const res = await sdk.pvInsight.analyze({
      detection: { customer_id: 'Sibaya', severity_label: 'moderate' },
      top_n: 3,
    });
    assert.strictEqual(receivedPath, '/analyze');
    assert.strictEqual(receivedMethod, 'POST');
    assert.strictEqual(res.llm_analysis.status, 'completed');
    console.log('test_js_pv_insight_client: PASSED');
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
}

function test_js_pvinsight_config_from_env() {
  const prev = {
    ONA_MODE: process.env.ONA_MODE,
    PVINSIGHT_API_URL: process.env.PVINSIGHT_API_URL,
  };

  process.env.ONA_MODE = 'edge';
  process.env.PVINSIGHT_API_URL = 'http://localhost:8003';

  delete require.cache[require.resolve('../src/config.js')];
  const Config = require('../src/config.js');
  const config = new Config();

  assert.strictEqual(
    config.endpoints.pvinsight,
    'http://localhost:8003',
    'endpoints.pvinsight must be http://localhost:8003'
  );

  for (const [k, v] of Object.entries(prev)) {
    if (v === undefined) { delete process.env[k]; } else { process.env[k] = v; }
  }
  delete require.cache[require.resolve('../src/config.js')];
  console.log('test_js_pvinsight_config_from_env: PASSED');
}

(async () => {
  try {
    test_js_pvinsight_config_from_env();
    await test_js_get_model_observatory();
    await test_js_pv_insight_client();
    console.log('\nAll Issue #2 JS tests PASSED');
  } catch (err) {
    console.error('\nTest FAILED:', err.message);
    process.exit(1);
  }
})();
