/**
 * SDK Configuration Management
 */

/**
 * Canonical endpoint defaults — not intended to be overridden in normal use.
 */
const DEFAULT_ENDPOINTS = {
  inverterTelemetry: 'https://telemetry.api.asoba.co',
  oodaTerminal:      'https://ooda.api.asoba.co',
  partnerApi:        'https://partner.api.asoba.co',
  terminal:          'https://api.asoba.co',
  // Internal / advanced
  forecasting:       null,
  dataIngestion:     null,
  edgeRegistry:      null,
  energyAnalyst:     null,
  globalTraining:    null,
  interpolation:     null,
  weather:           null,
};

/**
 * SDK configuration.
 *
 * The only required value is apiKey (or ASOBA_API_KEY environment variable).
 * All endpoint URLs default to the canonical production values.
 */
class Config {
  /**
   * @param {Object} [options]
   * @param {string} [options.apiKey]  - API key for telemetry, OODA, and partner APIs.
   *                                     Falls back to process.env.ASOBA_API_KEY.
   * @param {number} [options.timeout]     - Request timeout ms (default 30000).
   * @param {number} [options.retries]     - Retry count (default 3).
   * @param {number} [options.retryDelay]  - Retry delay ms (default 1000).
   * @param {Object} [options.endpoints]   - Override specific endpoint URLs (advanced).
   * @param {Object} [options.credentials] - AWS credentials for internal Lambda clients.
   */
  constructor(options = {}) {
    this.apiKey = options.apiKey || process.env.ASOBA_API_KEY || null;
    this.timeout = options.timeout || 30000;
    this.retries = options.retries !== undefined ? options.retries : 3;
    this.retryDelay = options.retryDelay || 1000;
    this.credentials = options.credentials || null;

    this.endpoints = {
      ...DEFAULT_ENDPOINTS,
      ...(options.endpoints || {}),
    };
  }

  /**
   * Get endpoint for a service.
   * @param {string} serviceName
   * @returns {string|null}
   */
  getEndpoint(serviceName) {
    return this.endpoints[serviceName] || null;
  }

  /**
   * Override endpoint for a service.
   * @param {string} serviceName
   * @param {string} endpoint
   */
  setEndpoint(serviceName, endpoint) {
    this.endpoints[serviceName] = endpoint;
  }

  /**
   * Check if AWS credentials are configured (for internal Lambda clients).
   * @returns {boolean}
   */
  hasCredentials() {
    return !!(this.credentials &&
      this.credentials.accessKeyId &&
      this.credentials.secretAccessKey);
  }

  /**
   * Get AWS credentials.
   * @returns {Object|null}
   */
  getCredentials() {
    return this.credentials;
  }
}

module.exports = Config;
