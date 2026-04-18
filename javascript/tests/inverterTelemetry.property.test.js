/**
 * Property-based tests for InverterTelemetryClient (JavaScript SDK)
 * Feature: inverter-telemetry-streaming
 * Uses fast-check for property generation and real local HTTP servers for network tests.
 */

'use strict';

const http = require('http');
const fc = require('fast-check');
const CursorSerializer = require('../src/utils/cursorSerializer');
const { parseTelemetryRecord } = require('../src/utils/telemetryRecord');
const { InverterTelemetryClient } = require('../src/services/InverterTelemetryClient');
const { ValidationError, ConfigurationError, AuthenticationError } = require('../src/utils/errors');

// Helper: start a local HTTP server with a given handler, returns { server, port, close }
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

// Helper: make a minimal valid telemetry record
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

// Helper: create a client pointing at a local http server (bypasses https check via direct endpoint override)
function makeTestClient(port, overrides = {}) {
  // We bypass the https check by constructing with a fake https endpoint then monkey-patching
  const client = Object.create(InverterTelemetryClient.prototype);
  client._endpoint = `http://127.0.0.1:${port}`;
  client._apiKey = 'test-api-key';
  client._pollingInterval = 5;
  client._retries = 0;
  client._activeStreams = new Set();
  Object.assign(client, overrides);
  return client;
}

// ─── Property 1: Cursor round-trip ───────────────────────────────────────────
// Feature: inverter-telemetry-streaming, Property 1: Cursor round-trip
test('Property 1: serialize then deserialize produces equivalent cursor object', () => {
  fc.assert(
    fc.property(
      fc.string({ minLength: 1, maxLength: 50 }),
      fc.string({ minLength: 1, maxLength: 50 }),
      (asset_id, timestamp) => {
        const serialized = CursorSerializer.serialize(asset_id, timestamp);
        const result = CursorSerializer.deserialize(serialized);
        expect(result.asset_id).toBe(asset_id);
        expect(result.timestamp).toBe(timestamp);
      }
    ),
    { numRuns: 200 }
  );
});

// ─── Property 2: Malformed cursor always throws ValidationError ───────────────
// Feature: inverter-telemetry-streaming, Property 2: Malformed cursor always throws ValidationError
test('Property 2: malformed cursor always throws ValidationError', () => {
  // Strings that are not valid serialized cursors
  const malformedArb = fc.oneof(
    // Random bytes encoded as base64url that won't decode to valid JSON object with required fields
    fc.string({ minLength: 0, maxLength: 20 }).map(s => Buffer.from(s).toString('base64url') + '!!!'),
    // Valid base64url but missing fields
    fc.record({ foo: fc.string() }).map(obj => Buffer.from(JSON.stringify(obj)).toString('base64url')),
    // Plain random strings
    fc.string({ minLength: 1, maxLength: 30 }).filter(s => {
      try {
        const d = CursorSerializer.deserialize(s);
        return false; // valid cursor, skip
      } catch {
        return true;
      }
    }),
  );

  fc.assert(
    fc.property(malformedArb, (cursor) => {
      expect(() => CursorSerializer.deserialize(cursor)).toThrow(ValidationError);
    }),
    { numRuns: 200 }
  );
});

// ─── Property 6: Inverted time range always throws ValidationError ────────────
// Feature: inverter-telemetry-streaming, Property 6: Inverted time range always throws ValidationError
test('Property 6: inverted time range always throws ValidationError', async () => {
  await fc.assert(
    fc.asyncProperty(
      fc.date({ min: new Date('2020-01-01'), max: new Date('2025-12-31') }),
      fc.date({ min: new Date('2020-01-01'), max: new Date('2025-12-31') }),
      async (d1, d2) => {
        // Skip NaN or invalid dates
        if (isNaN(d1.getTime()) || isNaN(d2.getTime())) return;
        // Ensure start > end
        const start = d1 > d2 ? d1 : d2;
        const end = d1 > d2 ? d2 : d1;
        if (start.getTime() === end.getTime()) return; // skip equal dates

        const client = makeTestClient(9999); // port doesn't matter, no network call
        const time_range = { start: start.toISOString(), end: end.toISOString() };

        await expect(
          client.getInverterTelemetry({ site_id: 'SiteA', time_range, limit: 10 })
        ).rejects.toThrow(ValidationError);
      }
    ),
    { numRuns: 100 }
  );
});

// ─── Property 7: Stream yields only strictly newer records ────────────────────
// Feature: inverter-telemetry-streaming, Property 7: Stream yields only strictly newer records
test('Property 7: stream yields only strictly newer records', async () => {
  // Two poll responses: first has records at t1, t2; second has t1, t2, t3
  const t1 = '2025-01-01T00:00:00';
  const t2 = '2025-01-01T00:05:00';
  const t3 = '2025-01-01T00:10:00';

  let callCount = 0;
  const srv = await startServer((req, res) => {
    callCount++;
    let records;
    if (callCount === 1) {
      records = [makeRecord({ timestamp: t1 }), makeRecord({ timestamp: t2 })];
    } else {
      records = [makeRecord({ timestamp: t1 }), makeRecord({ timestamp: t2 }), makeRecord({ timestamp: t3 })];
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ records }));
  });

  try {
    const client = makeTestClient(srv.port, { _pollingInterval: 0.001 });
    const yielded = [];
    const gen = client.streamInverter({ asset_id: 'INV-001', site_id: 'SiteA', polling_interval: 5 });

    // Override polling interval to 0 for test speed
    client._pollingInterval = 0;

    // Collect records from 2 poll cycles
    let iterations = 0;
    for await (const record of gen) {
      yielded.push(record);
      iterations++;
      if (iterations >= 3) break; // t1, t2 from first poll, t3 from second
    }

    // Should have t1, t2, t3 — no duplicates
    const timestamps = yielded.map(r => r.timestamp);
    expect(timestamps).toEqual([t1, t2, t3]);

    // Verify strictly increasing
    for (let i = 1; i < timestamps.length; i++) {
      expect(timestamps[i] > timestamps[i - 1]).toBe(true);
    }
  } finally {
    await srv.close();
  }
}, 15000);

// ─── Property 8: Every streamed record has a non-null cursor ─────────────────
// Feature: inverter-telemetry-streaming, Property 8: Every streamed record carries a non-null cursor
test('Property 8: every streamed record has a non-null cursor', async () => {
  const records = [
    makeRecord({ timestamp: '2025-01-01T00:00:00' }),
    makeRecord({ timestamp: '2025-01-01T00:05:00' }),
    makeRecord({ timestamp: '2025-01-01T00:10:00' }),
  ];

  let served = false;
  const srv = await startServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    if (!served) {
      served = true;
      res.end(JSON.stringify({ records }));
    } else {
      res.end(JSON.stringify({ records: [] }));
    }
  });

  try {
    const client = makeTestClient(srv.port);
    const yielded = [];
    const gen = client.streamInverter({ asset_id: 'INV-001', site_id: 'SiteA', polling_interval: 5 });

    let count = 0;
    for await (const record of gen) {
      yielded.push(record);
      count++;
      if (count >= 3) break;
    }

    for (const record of yielded) {
      expect(record.cursor).not.toBeNull();
      expect(typeof record.cursor).toBe('string');
      expect(record.cursor.length).toBeGreaterThan(0);
    }
  } finally {
    await srv.close();
  }
}, 15000);

// ─── Property 12: Every request has x-api-key header; no AWS auth headers ────
// Feature: inverter-telemetry-streaming, Property 12: Every request has x-api-key header; no AWS auth headers
test('Property 12: every request carries x-api-key header and no AWS auth headers', async () => {
  await fc.assert(
    fc.asyncProperty(
      // Use printable ASCII strings with no leading/trailing whitespace (HTTP headers trim whitespace)
      fc.string({ minLength: 5, maxLength: 40 }).filter(s => s.trim() === s && s.trim().length > 0),
      async (apiKey) => {
        const receivedHeaders = [];
        const srv = await startServer((req, res) => {
          receivedHeaders.push({ ...req.headers });
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ records: [] }));
        });

        try {
          const client = makeTestClient(srv.port);
          client._apiKey = apiKey;

          await client.getInverterTelemetry({
            site_id: 'SiteA',
            time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
          });

          expect(receivedHeaders.length).toBeGreaterThan(0);
          const headers = receivedHeaders[0];
          expect(headers['x-api-key']).toBe(apiKey);
          expect(headers['authorization']).toBeUndefined();
          expect(headers['x-amz-security-token']).toBeUndefined();
          expect(headers['x-amz-date']).toBeUndefined();
        } finally {
          await srv.close();
        }
      }
    ),
    { numRuns: 20 }
  );
}, 30000);

// ─── Property 13: Non-HTTPS endpoint always throws ConfigurationError ─────────
// Feature: inverter-telemetry-streaming, Property 13: Non-HTTPS endpoint always throws ConfigurationError
test('Property 13: non-HTTPS endpoint always throws ConfigurationError', () => {
  fc.assert(
    fc.property(
      fc.oneof(
        fc.constant('http://example.com'),
        fc.constant('ftp://example.com'),
        fc.constant('ws://example.com'),
        fc.string({ minLength: 1, maxLength: 30 }).filter(s => !s.startsWith('https://')),
      ),
      (endpoint) => {
        expect(() => new InverterTelemetryClient({
          endpoints: { inverterTelemetry: endpoint },
          inverterTelemetryApiKey: 'test-key',
        })).toThrow(ConfigurationError);
      }
    ),
    { numRuns: 100 }
  );
});

// ─── Property 14: limit > 1000 always throws ValidationError ─────────────────
// Feature: inverter-telemetry-streaming, Property 14: limit > 1000 always throws ValidationError
test('Property 14: limit > 1000 always throws ValidationError', async () => {
  await fc.assert(
    fc.asyncProperty(
      fc.integer({ min: 1001, max: 100000 }),
      async (limit) => {
        const client = makeTestClient(9999);
        await expect(
          client.getInverterTelemetry({
            site_id: 'SiteA',
            time_range: { start: '2025-01-01T00:00:00', end: '2025-01-02T00:00:00' },
            limit,
          })
        ).rejects.toThrow(ValidationError);
      }
    ),
    { numRuns: 100 }
  );
});

// ─── Property 15: Time range > 31 days always throws ValidationError ──────────
// Feature: inverter-telemetry-streaming, Property 15: Time range > 31 days always throws ValidationError
test('Property 15: time range > 31 days always throws ValidationError', async () => {
  await fc.assert(
    fc.asyncProperty(
      fc.integer({ min: 32, max: 365 }),
      async (days) => {
        const client = makeTestClient(9999);
        const start = new Date('2024-01-01T00:00:00Z');
        const end = new Date(start.getTime() + days * 24 * 60 * 60 * 1000);
        await expect(
          client.getInverterTelemetry({
            site_id: 'SiteA',
            time_range: { start: start.toISOString(), end: end.toISOString() },
          })
        ).rejects.toThrow(ValidationError);
      }
    ),
    { numRuns: 100 }
  );
});

// ─── Property 16: pollingInterval < 5 always throws ValidationError ───────────
// Feature: inverter-telemetry-streaming, Property 16: polling_interval < 5 s always throws ValidationError
test('Property 16: polling_interval < 5 always throws ValidationError', async () => {
  await fc.assert(
    fc.asyncProperty(
      fc.float({ min: 0, max: Math.fround(4.99), noNaN: true }),
      async (interval) => {
        const client = makeTestClient(9999);
        const gen = client.streamInverter({
          asset_id: 'INV-001',
          site_id: 'SiteA',
          polling_interval: interval,
        });
        await expect(gen.next()).rejects.toThrow(ValidationError);
      }
    ),
    { numRuns: 100 }
  );
});
