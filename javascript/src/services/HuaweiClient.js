/**
 * Huawei Data Client
 * Handles Huawei inverter data (historical and real-time)
 */

/**
 * Client for Huawei Services
 */
class HuaweiClient {
  /**
   * Create a new HuaweiClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.historicalEndpoint = config.getEndpoint('huaweiHistorical');
    this.realTimeEndpoint = config.getEndpoint('huaweiRealTime');
  }

  /**
   * Get historical Huawei data
   * @param {Object} payload - Request payload
   * @returns {Promise<Object>} Historical data
   */
  async getHistoricalData(payload) {
    return this.client.post(this.historicalEndpoint, payload, { signRequest: true });
  }

  /**
   * Get real-time Huawei data
   * @param {Object} payload - Request payload
   * @returns {Promise<Object>} Real-time data
   */
  async getRealTimeData(payload) {
    return this.client.post(this.realTimeEndpoint, payload, { signRequest: true });
  }
}

module.exports = HuaweiClient;
