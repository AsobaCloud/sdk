/**
 * SDK Configuration Management
 */

const { ConfigurationError } = require('./utils/errors');

/**
 * Default configuration values
 */
const DEFAULTS = {
  region: 'af-south-1',
  timeout: 30000, // 30 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
  endpoints: {
    forecasting: null,
    dataIngestion: null,
    dataStandardization: null,
    edgeRegistry: null,
    energyAnalyst: null,
    enphaseHistorical: null,
    enphaseRealTime: null,
    huaweiHistorical: null,
    huaweiRealTime: null,
    globalTraining: null,
    interpolation: null,
    terminal: null,
    weather: null,
    inverterTelemetry: null,
    oodaTerminal: null
  }
};

/**
 * Configuration class for SDK
 */
class Config {
  /**
   * Create a new configuration
   * @param {Object} options - Configuration options
   * @param {string} [options.region] - AWS region
   * @param {Object} [options.credentials] - AWS credentials
   * @param {string} [options.credentials.accessKeyId] - AWS access key ID
   * @param {string} [options.credentials.secretAccessKey] - AWS secret access key
   * @param {string} [options.credentials.sessionToken] - AWS session token
   * @param {Object} [options.endpoints] - Service endpoints
   * @param {number} [options.timeout] - Request timeout in milliseconds
   * @param {number} [options.retries] - Number of retries for failed requests
   * @param {number} [options.retryDelay] - Delay between retries in milliseconds
   */
  constructor(options = {}) {
    this.region = options.region || DEFAULTS.region;
    this.credentials = options.credentials || null;
    this.timeout = options.timeout || DEFAULTS.timeout;
    this.retries = options.retries !== undefined ? options.retries : DEFAULTS.retries;
    this.retryDelay = options.retryDelay || DEFAULTS.retryDelay;

    // Merge custom endpoints with defaults
    this.endpoints = {
      ...DEFAULTS.endpoints,
      ...(options.endpoints || {})
    };

    this.inverterTelemetryApiKey = options.inverterTelemetryApiKey
      || process.env.INVERTER_TELEMETRY_API_KEY
      || null;
    this.telemetryPollingInterval = options.telemetryPollingInterval !== undefined
      ? options.telemetryPollingInterval
      : 5;
    // endpoint comes from options.endpoints.inverterTelemetry or env var
    if (!this.endpoints.inverterTelemetry && process.env.INVERTER_TELEMETRY_ENDPOINT) {
      this.endpoints.inverterTelemetry = process.env.INVERTER_TELEMETRY_ENDPOINT;
    }

    this.oodaTerminalApiKey = options.oodaTerminalApiKey
      || process.env.OODA_TERMINAL_API_KEY
      || null;
    this.oodaPollingInterval = options.oodaPollingInterval !== undefined
      ? options.oodaPollingInterval
      : 5;
    // endpoint comes from options.endpoints.oodaTerminal or env var
    if (!this.endpoints.oodaTerminal && process.env.OODA_TERMINAL_ENDPOINT) {
      this.endpoints.oodaTerminal = process.env.OODA_TERMINAL_ENDPOINT;
    }

    this.validate();
  }

  /**
   * Validate configuration
   * @throws {ConfigurationError} If configuration is invalid
   */
  validate() {
    // Validate region
    if (typeof this.region !== 'string' || this.region.length === 0) {
      throw new ConfigurationError('Region must be a non-empty string', ['region']);
    }

    // Validate timeout
    if (typeof this.timeout !== 'number' || this.timeout <= 0) {
      throw new ConfigurationError('Timeout must be a positive number', ['timeout']);
    }

    // Validate retries
    if (typeof this.retries !== 'number' || this.retries < 0) {
      throw new ConfigurationError('Retries must be a non-negative number', ['retries']);
    }

    // Validate credentials if provided
    if (this.credentials) {
      const missingFields = [];

      if (!this.credentials.accessKeyId) {
        missingFields.push('credentials.accessKeyId');
      }

      if (!this.credentials.secretAccessKey) {
        missingFields.push('credentials.secretAccessKey');
      }

      if (missingFields.length > 0) {
        throw new ConfigurationError(
          'AWS credentials require both accessKeyId and secretAccessKey',
          missingFields
        );
      }
    }

    // Validate inverterTelemetry endpoint scheme if set
    const itEndpoint = this.endpoints.inverterTelemetry;
    if (itEndpoint && !itEndpoint.startsWith('https://')) {
      throw new ConfigurationError(
        'inverterTelemetry endpoint must use https://',
        ['endpoints.inverterTelemetry']
      );
    }

    // Validate oodaTerminal endpoint scheme if set
    const otEndpoint = this.endpoints.oodaTerminal;
    if (otEndpoint && !otEndpoint.startsWith('https://')) {
      throw new ConfigurationError(
        'oodaTerminal endpoint must use https://',
        ['endpoints.oodaTerminal']
      );
    }
  }

  /**
   * Get endpoint for a service
   * @param {string} serviceName - Name of the service
   * @returns {string|null} Service endpoint URL
   */
  getEndpoint(serviceName) {
    return this.endpoints[serviceName] || null;
  }

  /**
   * Set endpoint for a service
   * @param {string} serviceName - Name of the service
   * @param {string} endpoint - Service endpoint URL
   */
  setEndpoint(serviceName, endpoint) {
    this.endpoints[serviceName] = endpoint;
  }

  /**
   * Check if credentials are configured
   * @returns {boolean} True if credentials are configured
   */
  hasCredentials() {
    return this.credentials !== null &&
           this.credentials.accessKeyId !== undefined &&
           this.credentials.secretAccessKey !== undefined;
  }

  /**
   * Get AWS credentials
   * @returns {Object|null} AWS credentials object
   */
  getCredentials() {
    return this.credentials;
  }
}

module.exports = Config;
