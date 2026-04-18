/**
 * Unit tests for InverterTelemetryClient (JavaScript SDK)
 * Uses real local HTTP servers — no mocks.
 */

'use strict';

const http = require('http');
const { InverterTelemetryClient } = require('../src/services/InverterTelemetryClient');
const { ValidationError, ConfigurationError, AuthenticationError } = require('../src/utils/errors');

// Helper: start a local HTTP server
function startServer(handler) {
  return new Promise((resolve) => {
    const server = http.createServer(handler);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({
        server,
        port,
        close: () => new Promise(res => server.close(res)),
      });
    });
  });
}

// Helper: create a test client pointing at a local http server
function makeTestClient(port, opts = {}) {
  const client = Object.create(InverterTelemetryClient.prototype);
  client._endpoint = `http://127.0.0.1:${port}`;
  client._apiKey = opts.apiKey || 'test-api-key';
  client._pollingInterval = 5;
  client._retries = opts.retries !== undefined ? opts.retries : 0;
  client._activeStreams = new Set();
  return client;
}

function makeRecord(overrides = {}) {
  return {
    asset_id: 'INV-001',
    site_id: 'SiteA',
    timestamp: '2025-01-01T00:00:00',
    power: 1.0,
    kWh: 0.5,
    inverter_state: 1,
    run_state: 1,
    ...overrides,
  };
}

// ─── HTTP 401 → AuthenticationError (no retry) ───────────────────────────────
test('HTTP 401 → AuthenticationError without retry', async () => {
  let callCount = 0;
  const srv = await startServer((req, res) => {
    callCount++;
    res.writeHead(401);
    res.end(JSON.stringify({ error: 'Unauthorized' }));
  });

  try {
    const client = makeTestClient(srv.port, { retries: 3 });
    await expect(
      client.getInverterTelemetry({
        site_id: 'SiteA',
        time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
      })
    ).rejects.toThrow(AuthenticationError);
    // Should not retry on 401
    expect(callCount).toBe(1);
  } finally {
    await srv.close();
  }
});

// ─── HTTP 403 → AuthenticationError (no retry) ───────────────────────────────
test('HTTP 403 → AuthenticationError without retry', async () => {
  let callCount = 0;
  const srv = await startServer((req, res) => {
    callCount++;
    res.writeHead(403);
    res.end(JSON.stringify({ error: 'Access denied' }));
  });

  try {
    const client = makeTestClient(srv.port, { retries: 3 });
    await expect(
      client.getInverterTelemetry({
        site_id: 'SiteA',
        time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
      })
    ).rejects.toThrow(AuthenticationError);
    expect(callCount).toBe(1);
  } finally {
    await srv.close();
  }
});

// ─── HTTP 429 → RateLimitError (no retry) ────────────────────────────────────
test('HTTP 429 → RateLimitError without retry', async () => {
  let callCount = 0;
  const srv = await startServer((req, res) => {
    callCount++;
    res.writeHead(429);
    res.end(JSON.stringify({ error: 'Too many requests' }));
  });

  try {
    const client = makeTestClient(srv.port, { retries: 3 });
    const { RateLimitError } = require('../src/services/InverterTelemetryClient');
    await expect(
      client.getInverterTelemetry({
        site_id: 'SiteA',
        time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
      })
    ).rejects.toThrow(RateLimitError);
    expect(callCount).toBe(1);
  } finally {
    await srv.close();
  }
});

// ─── HTTP 500 → retries then ServiceUnavailableError ─────────────────────────
test('HTTP 500 → retries then ServiceUnavailableError', async () => {
  let callCount = 0;
  const srv = await startServer((req, res) => {
    callCount++;
    res.writeHead(500);
    res.end(JSON.stringify({ error: 'Service unavailable' }));
  });

  try {
    const client = makeTestClient(srv.port, { retries: 2 });
    const { ServiceUnavailableError } = require('../src/services/InverterTelemetryClient');
    await expect(
      client.getInverterTelemetry({
        site_id: 'SiteA',
        time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
      })
    ).rejects.toThrow(ServiceUnavailableError);
    // Should retry: 1 initial + 2 retries = 3 total
    expect(callCount).toBe(3);
  } finally {
    await srv.close();
  }
}, 10000);

// ─── Missing API key → AuthenticationError at construction ───────────────────
test('missing API key → AuthenticationError at construction', () => {
  expect(() => new InverterTelemetryClient({
    endpoints: { inverterTelemetry: 'https://example.com' },
    inverterTelemetryApiKey: null,
  })).toThrow(AuthenticationError);
});

// ─── Concurrent stream for same asset_id → ValidationError ───────────────────
test('concurrent stream for same asset_id → ValidationError', async () => {
  let requestCount = 0;
  const srv = await startServer((req, res) => {
    requestCount++;
    // Hang the first request to keep the stream active
    setTimeout(() => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ records: [] }));
    }, 5000);
  });

  try {
    const client = makeTestClient(srv.port);
    // Manually add the stream key to simulate an active stream
    client._activeStreams.add('inverter:INV-001');

    const gen = client.streamInverter({ asset_id: 'INV-001', site_id: 'SiteA', polling_interval: 5 });
    await expect(gen.next()).rejects.toThrow(ValidationError);
  } finally {
    await srv.close();
  }
});

// ─── getInverterTelemetry returns parsed records ──────────────────────────────
test('getInverterTelemetry returns parsed records from real server response', async () => {
  const records = [
    makeRecord({ timestamp: '2025-01-01T00:00:00', kVArh: 0.1 }),
    makeRecord({ timestamp: '2025-01-01T00:05:00', temperature: 25.5 }),
  ];

  const srv = await startServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ records }));
  });

  try {
    const client = makeTestClient(srv.port);
    const result = await client.getInverterTelemetry({
      site_id: 'SiteA',
      time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
    });

    expect(result).toHaveLength(2);
    expect(result[0].asset_id).toBe('INV-001');
    expect(result[0].timestamp).toBe('2025-01-01T00:00:00');
    expect(result[0].kVArh).toBe(0.1);
    expect(result[1].temperature).toBe(25.5);
    // expires_at should not be present
    expect(result[0].expires_at).toBeUndefined();
  } finally {
    await srv.close();
  }
});

// ─── getSiteTelemetry returns grouped records ─────────────────────────────────
test('getSiteTelemetry returns grouped records from real server response', async () => {
  const responseData = {
    records: {
      'INV-001': [makeRecord({ asset_id: 'INV-001', timestamp: '2025-01-01T00:00:00' })],
      'INV-002': [makeRecord({ asset_id: 'INV-002', timestamp: '2025-01-01T00:05:00' })],
    },
  };

  const srv = await startServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(responseData));
  });

  try {
    const client = makeTestClient(srv.port);
    const result = await client.getSiteTelemetry({
      site_id: 'SiteA',
      time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
    });

    expect(Object.keys(result)).toHaveLength(2);
    expect(result['INV-001']).toHaveLength(1);
    expect(result['INV-002']).toHaveLength(1);
    expect(result['INV-001'][0].asset_id).toBe('INV-001');
    expect(result['INV-002'][0].asset_id).toBe('INV-002');
  } finally {
    await srv.close();
  }
});
