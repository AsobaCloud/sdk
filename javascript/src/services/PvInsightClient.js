/**
 * PVInsight Service Client (JEPA to RAG Nehanda synthesis)
 */

'use strict';

const { validateRequired } = require('../utils/validators');

class PvInsightClient {
  /**
   * Create a new PvInsightClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('pvinsight') || 'http://localhost:8003';
  }

  /**
   * Analyze a JEPA anomaly detection and generate grounded O&M recommendations.
   * @param {Object} params - Analysis parameters
   * @param {Object} params.detection - JEPA detection object
   * @param {number} [params.top_n=5] - Number of retrieved chunks to consider
   * @param {string} [params.min_severity='minor'] - Minimum severity threshold
   * @param {string} [params.job_id=null] - Optional async job ID
   * @returns {Promise<Object>} Enriched detection with llm_analysis
   */
  async analyze({ detection, top_n = 5, min_severity = 'minor', job_id = null }) {
    validateRequired({ detection }, ['detection']);
    const payload = {
      detection,
      top_n,
      min_severity,
    };
    if (job_id !== null && job_id !== undefined) {
      payload.job_id = job_id;
    }
    return this.client.post(`${this.endpoint}/analyze`, payload, {
      signRequest: !this.config.isEdge(),
    });
  }

  /**
   * Health check for pvInsightService.
   * @returns {Promise<Object>} Service health status
   */
  async health() {
    return this.client.get(`${this.endpoint}/health`, {}, {
      signRequest: !this.config.isEdge(),
    });
  }
}

module.exports = PvInsightClient;
