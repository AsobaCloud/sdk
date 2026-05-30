/**
 * Gap Detection Client
 * Identifies missing data intervals and triggers targeted backfill
 */

class GapDetectionClient {
  /**
   * Create a new GapDetectionClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('gapDetection');
  }

  /**
   * Run gap detection scan
   * @param {Object} params - Scan parameters
   * @returns {Promise<Object>} Detection results
   */
  async detectGaps(params) {
    return this.client.post(this.endpoint, params, { signRequest: true });
  }
}

module.exports = GapDetectionClient;
