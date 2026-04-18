/**
 * Interpolation Service Client
 * Handles ML-based data interpolation with weather enrichment
 */

/**
 * Client for Interpolation Service
 */
class InterpolationClient {
  /**
   * Create a new InterpolationClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('interpolation');
  }

  /**
   * Invoke interpolation service
   * @param {Object} payload - Interpolation payload
   * @returns {Promise<Object>} Interpolation result
   */
  async interpolate(payload) {
    return this.client.post(this.endpoint, payload, { signRequest: true });
  }
}

module.exports = InterpolationClient;
