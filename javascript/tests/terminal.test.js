const TerminalClient = require('../src/services/TerminalClient');
const { OnaSDK } = require('../src/index');

// ---------------------------------------------------------------------------
// JEPA fixture — copied from platform/ui/tests/test_pv_insight_e2e_behavioral.js
// ---------------------------------------------------------------------------
const JEPA_DETECTION = {
  asset_id: 'INV-BN2441041190',
  severity_label: 'high',
  severity_score: 0.82,
  fault_type: 'behavioral_anomaly',
  summary: 'Inverter 1 - World model anomaly score 0.0891 (Streak: 6)',
  metrics: {
    latest_power_kw: 45.2,
    baseline_power_kw: 280.5,
    latest_temperature_c: 68.3,
    latest_inverter_state: 513,
    world_model_streak_length: 6,
  },
  energy_at_risk_kw: 235.3,
};

describe('TerminalClient', () => {
  let mockHttpClient;
  let mockConfig;
  let client;

  beforeEach(() => {
    mockHttpClient = {
      post: jest.fn(),
    };
    mockConfig = {
      getEndpoint: jest.fn().mockReturnValue('https://terminal-api.example.com'),
    };
    client = new TerminalClient(mockHttpClient, mockConfig);
  });

  describe('calculateRemainingWarrantyLife', () => {
    // Use UTC for today to match implementation
    const now = new Date();
    const todayUTC = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));

    test('should return in_warranty for healthy battery', () => {
      const expiry = new Date(todayUTC);
      expiry.setUTCDate(todayUTC.getUTCDate() + 100);
      const expiryStr = expiry.toISOString().split('T')[0];

      const res = TerminalClient.calculateRemainingWarrantyLife({
        warranty_expiry_date: expiryStr,
        warranty_throughput_kwh: 1000,
        current_throughput_kwh: 500,
      });

      expect(res.warranty_status).toBe('in_warranty');
      expect(res.days_remaining).toBe(100);
      expect(res.throughput_remaining_pct).toBe(50.0);
      expect(res.limiting_factor).toBe('date');
    });

    test('should return expiring_soon for date < 90 days', () => {
      const expiry = new Date(todayUTC);
      expiry.setUTCDate(todayUTC.getUTCDate() + 30);
      const expiryStr = expiry.toISOString().split('T')[0];

      const res = TerminalClient.calculateRemainingWarrantyLife({
        warranty_expiry_date: expiryStr,
        warranty_throughput_kwh: 1000,
        current_throughput_kwh: 500,
      });

      expect(res.warranty_status).toBe('expiring_soon');
      expect(res.limiting_factor).toBe('date');
    });

    test('should return expiring_soon for throughput usage > 80%', () => {
      const expiry = new Date(todayUTC);
      expiry.setUTCDate(todayUTC.getUTCDate() + 200);
      const expiryStr = expiry.toISOString().split('T')[0];

      const res = TerminalClient.calculateRemainingWarrantyLife({
        warranty_expiry_date: expiryStr,
        warranty_throughput_kwh: 1000,
        current_throughput_kwh: 850,
      });

      expect(res.warranty_status).toBe('expiring_soon');
      expect(res.limiting_factor).toBe('throughput');
      expect(res.throughput_remaining_pct).toBe(15.0);
    });

    test('should return out_of_warranty for past date', () => {
      const expiry = new Date(todayUTC);
      expiry.setUTCDate(todayUTC.getUTCDate() - 1);
      const expiryStr = expiry.toISOString().split('T')[0];

      const res = TerminalClient.calculateRemainingWarrantyLife({
        warranty_expiry_date: expiryStr,
        warranty_throughput_kwh: 1000,
        current_throughput_kwh: 500,
      });

      expect(res.warranty_status).toBe('out_of_warranty');
    });

    test('should return unknown for missing data', () => {
      const res = TerminalClient.calculateRemainingWarrantyLife({
        warranty_expiry_date: null,
        warranty_throughput_kwh: null,
      });

      expect(res.warranty_status).toBe('unknown');
      expect(res.days_remaining).toBeNull();
      expect(res.throughput_remaining_pct).toBeNull();
    });
  });

  describe('getAsset', () => {
    test('should return null on 404', async () => {
      mockHttpClient.post.mockRejectedValue({ statusCode: 404 });
      const result = await client.getAsset({ customer_id: 'c1', asset_id: 'a1' });
      expect(result).toBeNull();
    });

    test('should return asset details on success', async () => {
      const mockAsset = { asset_id: 'a1', capacity_kwh: 10 };
      mockHttpClient.post.mockResolvedValue(mockAsset);
      const result = await client.getAsset({ customer_id: 'c1', asset_id: 'a1' });
      expect(result).toEqual(mockAsset);
    });
  });

  describe('getSiteSummary', () => {
    test('should return site summary with battery KPIs', async () => {
      const mockSummary = { site_id: 's1', battery: { avg_soc: 90 } };
      mockHttpClient.post.mockResolvedValue(mockSummary);
      const result = await client.getSiteSummary({ site_id: 's1' });
      expect(result).toEqual(mockSummary);
    });
  });
});

// ---------------------------------------------------------------------------
// BC-3 — live end-to-end test
// Run with: LIVE=1 npx jest terminal.test.js --testNamePattern="BC-3"
// Requires: env AWS credentials + terminal endpoint accessible
// ---------------------------------------------------------------------------

const RUN_LIVE = process.env.LIVE === '1';

(RUN_LIVE ? describe : describe.skip)('runPvInsightSynthesis — BC-3 live', () => {
  /**
   * BC-3: Live call to terminalApi pv-insight action via OnaSDK.
   *
   * Pass criteria (copied from platform/ui/tests/test_pv_insight_e2e_behavioral.js Step 3):
   * - llm_analysis is present in the response
   * - llm_analysis.status === 'ok'
   * - llm_analysis.recommendation is a string with length > 20
   * - llm_analysis.cited_sources is an array with length > 0
   */
  test('should return llm_analysis with ok status and recommendation', async () => {
    const sdk = new OnaSDK({
      region: 'af-south-1',
      credentials: {
        accessKeyId: process.env.AWS_ACCESS_KEY_ID,
        secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
        ...(process.env.AWS_SESSION_TOKEN && { sessionToken: process.env.AWS_SESSION_TOKEN }),
      },
      endpoints: {
        // UI e2e host + /terminal prefix (host api.asoba.co, path /terminal/detect)
        terminal: 'https://api.asoba.co/terminal',
      },
      timeout: 90000, // UI e2e req.setTimeout(90000); overrides JS default 30s
    });

    const result = await sdk.terminal.runPvInsightSynthesis({ detection: JEPA_DETECTION });

    expect(result).toHaveProperty('llm_analysis');
    const llm = result.llm_analysis;
    expect(llm.status).toBe('ok');
    expect(typeof llm.recommendation).toBe('string');
    expect(llm.recommendation.length).toBeGreaterThan(20);
    expect(Array.isArray(llm.cited_sources)).toBe(true);
    expect(llm.cited_sources.length).toBeGreaterThan(0);
  }, 90000); // jest timeout matches UI e2e
});

// ---------------------------------------------------------------------------
// Secondary — error-path tests using mock HTTP client
// ---------------------------------------------------------------------------

describe('runPvInsightSynthesis — secondary error paths', () => {
  let mockHttpClient;
  let mockConfig;
  let client;

  beforeEach(() => {
    mockHttpClient = { post: jest.fn() };
    mockConfig = { getEndpoint: jest.fn().mockReturnValue('https://terminal-api.example.com') };
    client = new TerminalClient(mockHttpClient, mockConfig);
  });

  test('missing detection should throw via SDK validation', async () => {
    // validateRequired({ detection }, ['detection']) throws when detection is undefined
    await expect(
      client.runPvInsightSynthesis({ detection: undefined })
    ).rejects.toThrow();
  });

  test('detection with invalid severity_label should surface HTTP error (mock 400)', async () => {
    const badDetection = { ...JEPA_DETECTION, severity_label: 'nope' };
    const httpError = Object.assign(new Error('Bad Request'), { statusCode: 400 });
    mockHttpClient.post.mockRejectedValue(httpError);

    await expect(
      client.runPvInsightSynthesis({ detection: badDetection })
    ).rejects.toMatchObject({ statusCode: 400 });
  });
});
