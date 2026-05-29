/**
 * Unit tests for PartnerApiClient (JavaScript SDK).
 *
 * Scope note: the JS PartnerApiClient is intentionally thin — it builds the
 * request URL + headers and forwards to a generic httpClient. ETag caching
 * and status-code → typed-error mapping live in the HTTP layer (or are
 * out-of-scope for this client). These tests cover what PartnerApiClient
 * itself does: URL construction, query-param threading, config guards.
 * The Python equivalent has richer in-client logic and gets richer tests
 * in tests/test_partner_api_client.py.
 */

'use strict';

const PartnerApiClient = require('../src/services/PartnerApiClient');
const {
  ConfigurationError,
  AuthenticationError,
} = require('../src/utils/errors');

// ---------------------------------------------------------------------------
// Sample payload matching the live S3 snapshot shape
// ---------------------------------------------------------------------------

const SCHEDULE_PAYLOAD = {
  site_id: 'Sibaya',
  generated_at: '2026-05-29T13:27:11.985596+00:00',
  horizon: { start: '2026-05-29', end: '2026-08-27' },
  tasks: [
    {
      asset_id: 'INV-1000000054495190',
      task_type: 'inspection',
      reason: '33 anomalies detected in the last 2 days',
      recommended_date: '2026-06-05',
      estimated_duration_hours: 2.0,
      priority: 'High',
    },
  ],
  summary: {
    total_tasks: 1,
    by_priority: { High: 1 },
    by_task_type: { inspection: 1 },
    by_asset: { 'INV-1000000054495190': 1 },
  },
};

// ---------------------------------------------------------------------------
// Spy httpClient that records the URL it's called with
// ---------------------------------------------------------------------------

function makeSpyClient(returnValue = SCHEDULE_PAYLOAD) {
  const calls = [];
  const httpClient = {
    get: jest.fn(async (url, options) => {
      calls.push({ url, options });
      return returnValue;
    }),
  };
  return { httpClient, calls };
}

function makeClient(httpClient, partnerApi = 'https://api.example.com') {
  return new PartnerApiClient(httpClient, {
    endpoints: { partnerApi },
    partnerApiKey: 'test-key',
  });
}

// ---------------------------------------------------------------------------
// Config + auth guards
// ---------------------------------------------------------------------------

describe('PartnerApiClient — config guards', () => {
  test('EH1 missing partnerApi endpoint throws ConfigurationError', () => {
    const { httpClient } = makeSpyClient();
    expect(
      () =>
        new PartnerApiClient(httpClient, {
          endpoints: {},
          partnerApiKey: 'k',
        })
    ).toThrow(ConfigurationError);
  });

  test('EH1 non-https endpoint throws ConfigurationError', () => {
    const { httpClient } = makeSpyClient();
    expect(
      () =>
        new PartnerApiClient(httpClient, {
          endpoints: { partnerApi: 'http://example.com' },
          partnerApiKey: 'k',
        })
    ).toThrow(ConfigurationError);
  });

  test('EH2 missing api key throws AuthenticationError', () => {
    const { httpClient } = makeSpyClient();
    expect(
      () =>
        new PartnerApiClient(httpClient, {
          endpoints: { partnerApi: 'https://example.com' },
        })
    ).toThrow(AuthenticationError);
  });
});

// ---------------------------------------------------------------------------
// getMaintenanceSchedule (SEP-062)
// ---------------------------------------------------------------------------

describe('PartnerApiClient.getMaintenanceSchedule — SEP-062', () => {
  test('HP1 returns whatever the httpClient returns', async () => {
    const { httpClient } = makeSpyClient(SCHEDULE_PAYLOAD);
    const client = makeClient(httpClient);
    const result = await client.getMaintenanceSchedule({ site_id: 'Sibaya' });
    expect(result).toEqual(SCHEDULE_PAYLOAD);
  });

  test('IB1 hits /maintenance-schedule path', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getMaintenanceSchedule({ site_id: 'Sibaya' });
    const u = new URL(calls[0].url);
    expect(u.pathname).toBe('/maintenance-schedule');
  });

  test('IB2 site_id sent as query string', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getMaintenanceSchedule({ site_id: 'CapeTown' });
    const u = new URL(calls[0].url);
    expect(u.searchParams.get('site_id')).toBe('CapeTown');
  });

  test('HP1 since param threads through', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getMaintenanceSchedule({
      site_id: 'Sibaya',
      since: '2026-05-01T00:00:00',
    });
    const u = new URL(calls[0].url);
    expect(u.searchParams.get('since')).toBe('2026-05-01T00:00:00');
  });

  test('x-api-key header is sent', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getMaintenanceSchedule({ site_id: 'Sibaya' });
    expect(calls[0].options.headers['x-api-key']).toBe('test-key');
  });

  test('omitted since does NOT appear in the query string', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getMaintenanceSchedule({ site_id: 'Sibaya' });
    const u = new URL(calls[0].url);
    expect(u.searchParams.has('since')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Regression: existing 3 methods still construct correct URLs
// ---------------------------------------------------------------------------

describe('PartnerApiClient — existing-methods regression', () => {
  test('INV2 getKpiRollup hits /kpi-rollup', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getKpiRollup({ site_id: 'Sibaya' });
    expect(new URL(calls[0].url).pathname).toBe('/kpi-rollup');
  });

  test('INV2 getMaintenanceSignals hits /maintenance-signals', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getMaintenanceSignals({ site_id: 'Sibaya' });
    expect(new URL(calls[0].url).pathname).toBe('/maintenance-signals');
  });

  test('INV2 getForecastSnapshot hits /forecast-snapshot', async () => {
    const { httpClient, calls } = makeSpyClient();
    const client = makeClient(httpClient);
    await client.getForecastSnapshot({ site_id: 'Sibaya' });
    expect(new URL(calls[0].url).pathname).toBe('/forecast-snapshot');
  });
});
