/**
 * Weather Cache Client
 * Handles weather data caching and updates
 */

/**
 * Client for Weather Cache Service
 */
class WeatherClient {
  /**
   * Create a new WeatherClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('weather');
  }

  /**
   * Trigger weather cache update
   * @param {Object} payload - Update payload
   * @returns {Promise<Object>} Update result
   */
  async updateCache(payload) {
    return this.client.post(this.endpoint, payload, { signRequest: true });
  }
}

module.exports = WeatherClient;
