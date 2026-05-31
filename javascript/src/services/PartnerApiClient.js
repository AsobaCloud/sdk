const { ConfigurationError, AuthenticationError } = require('../utils/errors');

/**
 * Client for the Partner API.
 * Provides access to pre-computed JSON snapshots for embedding and partner integrations.
 */
class PartnerApiClient {
  /**
   * Create a new Partner API client.
   * @param {HTTPClient} httpClient - The HTTP client to use for requests.
   * @param {Config} config - SDK configuration.
   */
  constructor(httpClient, config) {
    this.httpClient = httpClient;
    this.config = config;

    this.endpoint = this.config.endpoints.partnerApi;
    this.apiKey = this.config.partnerApiKey;

    if (!this.endpoint) {
      throw new ConfigurationError('partnerApi endpoint is required', [
        'endpoints.partnerApi',
      ]);
    }
    if (!this.endpoint.startsWith('https://')) {
      throw new ConfigurationError('partnerApi endpoint must use https://', [
        'endpoints.partnerApi',
      ]);
    }
    if (!this.apiKey) {
      throw new AuthenticationError('partnerApiKey is required');
    }

    this.endpoint = this.endpoint.replace(/\/$/, '');
  }

  /**
   * Internal request helper.
   * @private
   */
  async _request(path, site_id, extraParams = {}) {
    const url = new URL(this.endpoint + path);
    if (site_id) {
      url.searchParams.set('site_id', site_id);
    }
    for (const [k, v] of Object.entries(extraParams)) {
      if (v !== undefined && v !== null) {
        url.searchParams.set(k, String(v));
      }
    }

    return this.httpClient.get(url.toString(), {
      headers: {
        'x-api-key': this.apiKey,
        'Accept': 'application/json',
      },
    });
  }

  /**
   * Get the latest KPI Rollup snapshot for a site.
   *
   * The KPI rollup includes energy balance, performance, availability,
   * financial metrics, and battery health KPIs (avg_soc, avg_soh,
   * total_capacity_kwh, warranty_status, throughput_kwh, etc.) for sites
   * with battery assets.
   *
   * @param {Object} params - Parameters
   * @param {string} params.site_id - Site identifier
   * @returns {Promise<Object>} KPI Rollup snapshot
   */
  async getKpiRollup({ site_id }) {
    return this._request('/kpi-rollup', site_id);
  }

  /**
   * Get maintenance signals for a site.
   * @param {Object} params - Parameters
   * @param {string} params.site_id - Site identifier
   * @param {string} [params.since] - Optional cursor/timestamp to fetch signals since
   * @param {string} [params.severity] - Optional severity filter
   * @returns {Promise<Object>} Maintenance signals snapshot
   */
  async getMaintenanceSignals({ site_id, since, severity } = {}) {
    return this._request('/maintenance-signals', site_id, { since, severity });
  }

  /**
   * Get the latest forecast snapshot for a site.
   * @param {Object} params - Parameters
   * @param {string} params.site_id - Site identifier
   * @param {string} [params.horizon] - Optional forecast horizon
   * @returns {Promise<Object>} Forecast snapshot
   */
  async getForecastSnapshot({ site_id, horizon } = {}) {
    return this._request('/forecast-snapshot', site_id, { horizon });
  }

  /**
   * Get the preventive-maintenance schedule snapshot for a site (SEP-062).
   *
   * Returns a forward-looking 90-day task list grouped by inverter, derived
   * from rolling-window anomaly frequency and configurable manufacturer
   * service intervals. Companion to getMaintenanceSignals().
   *
   * @param {Object} params - Parameters
   * @param {string} params.site_id - Site identifier
   * @param {string} [params.since] - Optional ISO timestamp filter
   * @returns {Promise<Object>} Maintenance schedule snapshot
   */
  async getMaintenanceSchedule({ site_id, since } = {}) {
    return this._request('/maintenance-schedule', site_id, { since });
  }

  /**
   * Get a generic snapshot for a site.
   * @param {Object} params - Parameters
   * @param {string} params.site_id - Site identifier
   * @param {string} params.kind - The kind of snapshot to fetch
   * @returns {Promise<Object>} Snapshot data
   */
  async getSnapshot({ site_id, kind, ...rest } = {}) {
    return this._request('/snapshot', site_id, { kind, ...rest });
  }
}

module.exports = PartnerApiClient;
