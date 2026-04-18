/**
 * Enphase Data Client
 * Handles Enphase inverter data (historical and real-time)
 */

/**
 * Client for Enphase Services
 */
class EnphaseClient {
  /**
   * Create a new EnphaseClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.historicalEndpoint = config.getEndpoint('enphaseHistorical');
    this.realTimeEndpoint = config.getEndpoint('enphaseRealTime');
  }

  /**
   * Get historical Enphase data
   * @param {Object} payload - Request payload
   * @returns {Promise<Object>} Historical data
   */
  async getHistoricalData(payload) {
    return this.client.post(this.historicalEndpoint, payload, { signRequest: true });
  }

  /**
   * Get real-time Enphase data
   * @param {Object} payload - Request payload
   * @returns {Promise<Object>} Real-time data
   */
  async getRealTimeData(payload) {
    return this.client.post(this.realTimeEndpoint, payload, { signRequest: true });
  }
}

module.exports = EnphaseClient;
