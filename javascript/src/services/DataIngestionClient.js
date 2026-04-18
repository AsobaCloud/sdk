/**
 * Data Ingestion Client
 * Handles data ingestion and preprocessing
 */

/**
 * Client for Data Ingestion Service
 */
class DataIngestionClient {
  /**
   * Create a new DataIngestionClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('dataIngestion');
  }

  /**
   * Invoke data ingestion service
   * @param {Object} payload - Ingestion payload
   * @returns {Promise<Object>} Ingestion result
   */
  async ingest(payload) {
    return this.client.post(this.endpoint, payload, { signRequest: true });
  }
}

module.exports = DataIngestionClient;
