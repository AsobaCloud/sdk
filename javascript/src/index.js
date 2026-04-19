/**
 * Asoba Ona Energy Management Platform SDK
 * Official JavaScript SDK for interacting with Ona platform services
 */

const Config = require('./config');
const HTTPClient = require('./client');

// Service clients
const ForecastingClient = require('./services/ForecastingClient');
const TerminalClient = require('./services/TerminalClient');
const EnergyAnalystClient = require('./services/EnergyAnalystClient');
const EdgeDeviceRegistryClient = require('./services/EdgeDeviceRegistryClient');
const DataIngestionClient = require('./services/DataIngestionClient');
const InterpolationClient = require('./services/InterpolationClient');
const WeatherClient = require('./services/WeatherClient');
const EnphaseClient = require('./services/EnphaseClient');
const HuaweiClient = require('./services/HuaweiClient');
const { InverterTelemetryClient, RateLimitError: ITRateLimitError, ServiceUnavailableError: ITServiceUnavailableError } = require('./services/InverterTelemetryClient');
const { OodaTerminalClient, RateLimitError: OTRateLimitError, ServiceUnavailableError: OTServiceUnavailableError } = require('./services/OodaTerminalClient');
const { FreemiumForecastClient } = require('./services/FreemiumForecastClient');

// Utilities
const errors = require('./utils/errors');
const validators = require('./utils/validators');

/**
 * Main SDK class
 */
class OnaSDK {
  /**
   * Create a new Ona SDK instance
   * @param {Object} options - SDK options
   * @param {string} [options.region='af-south-1'] - AWS region
   * @param {Object} [options.credentials] - AWS credentials
   * @param {string} [options.credentials.accessKeyId] - AWS access key ID
   * @param {string} [options.credentials.secretAccessKey] - AWS secret access key
   * @param {string} [options.credentials.sessionToken] - AWS session token
   * @param {Object} [options.endpoints] - Service endpoints
   * @param {number} [options.timeout=30000] - Request timeout in milliseconds
   * @param {number} [options.retries=3] - Number of retries for failed requests
   * @param {number} [options.retryDelay=1000] - Delay between retries in milliseconds
   *
   * @example
   * const sdk = new OnaSDK({
   *   region: 'af-south-1',
   *   credentials: {
   *     accessKeyId: 'YOUR_ACCESS_KEY',
   *     secretAccessKey: 'YOUR_SECRET_KEY'
   *   },
   *   endpoints: {
   *     forecasting: 'https://forecasting.api.asoba.co',
   *     terminal: 'https://terminal.api.asoba.co',
   *     edgeRegistry: 'http://edge-registry:8082',
   *     energyAnalyst: 'http://energy-analyst:8000'
   *   }
   * });
   */
  constructor(options = {}) {
    // Initialize configuration
    this.config = new Config(options);

    // Initialize HTTP client
    this.httpClient = new HTTPClient(this.config);

    // Initialize service clients
    this._initializeClients();
  }

  /**
   * Initialize all service clients
   * @private
   */
  _initializeClients() {
    /**
     * Forecasting API client
     * @type {ForecastingClient}
     */
    this.forecasting = new ForecastingClient(this.httpClient, this.config);

    /**
     * Terminal API client (OODA workflow)
     * @type {TerminalClient}
     */
    this.terminal = new TerminalClient(this.httpClient, this.config);

    /**
     * Energy Analyst RAG client
     * @type {EnergyAnalystClient}
     */
    this.energyAnalyst = new EnergyAnalystClient(this.httpClient, this.config);

    /**
     * Edge Device Registry client
     * @type {EdgeDeviceRegistryClient}
     */
    this.edgeRegistry = new EdgeDeviceRegistryClient(this.httpClient, this.config);

    /**
     * Data Ingestion client
     * @type {DataIngestionClient}
     */
    this.dataIngestion = new DataIngestionClient(this.httpClient, this.config);

    /**
     * Interpolation Service client
     * @type {InterpolationClient}
     */
    this.interpolation = new InterpolationClient(this.httpClient, this.config);

    /**
     * Weather Cache client
     * @type {WeatherClient}
     */
    this.weather = new WeatherClient(this.httpClient, this.config);

    /**
     * Enphase data client
     * @type {EnphaseClient}
     */
    this.enphase = new EnphaseClient(this.httpClient, this.config);

    /**
     * Huawei data client
     * @type {HuaweiClient}
     */
    this.huawei = new HuaweiClient(this.httpClient, this.config);

    /**
     * Inverter Telemetry client
     * @type {InverterTelemetryClient|null}
     */
    try {
      this.inverterTelemetry = new InverterTelemetryClient(this.config);
    } catch (e) {
      this.inverterTelemetry = null;
    }

    /**
     * OODA Terminal client
     * @type {OodaTerminalClient|null}
     */
    try {
      this.oodaTerminal = new OodaTerminalClient(this.config);
    } catch (e) {
      this.oodaTerminal = null;
    }

    /**
     * Freemium Forecast client (no API key required)
     * @type {FreemiumForecastClient}
     */
    this.freemiumForecast = new FreemiumForecastClient(this.config);
  }

  /**
   * Update service endpoint
   * @param {string} serviceName - Name of the service
   * @param {string} endpoint - New endpoint URL
   */
  setEndpoint(serviceName, endpoint) {
    this.config.setEndpoint(serviceName, endpoint);
  }

  /**
   * Get current configuration
   * @returns {Config} Current configuration
   */
  getConfig() {
    return this.config;
  }

  /**
   * Get SDK version
   * @returns {string} SDK version
   */
  static getVersion() {
    return '1.0.0';
  }
}

// Export SDK class and utilities
module.exports = {
  OnaSDK,
  InverterTelemetryClient,
  RateLimitError: ITRateLimitError,
  ServiceUnavailableError: ITServiceUnavailableError,
  OodaTerminalClient,
  OodaRateLimitError: OTRateLimitError,
  OodaServiceUnavailableError: OTServiceUnavailableError,
  FreemiumForecastClient,
  ...errors,
  ...validators
};
