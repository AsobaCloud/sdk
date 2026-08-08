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
const PartnerApiClient = require('./services/PartnerApiClient');
const InverterTelemetryClient = require('./services/InverterTelemetryClient');
const OodaTerminalClient = require('./services/OodaTerminalClient');

// Utilities
const errors = require('./utils/errors');
const validators = require('./utils/validators');

/**
 * Main SDK class
 */
class OnaSDK {
  /**
   * Create a new Ona SDK instance.
   *
   * @param {Object} [options]
   * @param {string} [options.apiKey] - API key for telemetry, OODA, and partner APIs.
   *   Falls back to process.env.ASOBA_API_KEY.
   * @param {number} [options.timeout=30000] - Request timeout ms.
   * @param {number} [options.retries=3] - Retry count.
   * @param {number} [options.retryDelay=1000] - Retry delay ms.
   * @param {Object} [options.endpoints] - Override specific endpoint URLs (advanced).
   * @param {Object} [options.credentials] - AWS credentials for internal Lambda clients.
   *
   * @example
   * // From environment variable ASOBA_API_KEY
   * const sdk = new OnaSDK();
   *
   * // Explicit key
   * const sdk = new OnaSDK({ apiKey: 'your_key' });
   */
  constructor(options = {}) {
    this.config = new Config(options);
    this.httpClient = new HTTPClient(this.config);
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
     * Partner API client (JSON snapshots)
     * @type {PartnerApiClient}
     */
    this.partner = new PartnerApiClient(this.httpClient, this.config);

    /**
     * Inverter Telemetry API client
     * @type {InverterTelemetryClient}
     */
    this.inverterTelemetry = new InverterTelemetryClient(this.config);

    /**
     * OODA Terminal Alerts API client
     * @type {OodaTerminalClient}
     */
    this.oodaTerminal = new OodaTerminalClient(this.config);
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
  ...errors,
  ...validators
};
