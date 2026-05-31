const TerminalClient = require('../src/services/TerminalClient');

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
