/**
 * Global Training Client
 * Manages ML model training and deployment workflows
 */

class GlobalTrainingClient {
  /**
   * Create a new GlobalTrainingClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('globalTraining');
  }

  /**
   * Trigger a training job
   * @param {Object} params - Training parameters
   * @returns {Promise<Object>} Job initiation result
   */
  async triggerTraining(params) {
    return this.client.post(this.endpoint, params, { signRequest: true });
  }

  /**
   * Get training job status
   * @param {string} customerId - Customer identifier
   * @returns {Promise<Object>} Current status and progress
   */
  async getTrainingStatus(customerId) {
    const url = new URL(this.endpoint + '/status');
    url.searchParams.set('customer_id', customerId);
    return this.client.get(url.toString(), { signRequest: true });
  }
}

module.exports = GlobalTrainingClient;
