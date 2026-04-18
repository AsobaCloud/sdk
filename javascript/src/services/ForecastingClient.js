/**
 * Forecasting API Client
 * Provides energy forecasting at device, site, and customer levels
 */

const {
  validateCustomerId,
  validateSiteId,
  validateDeviceId,
  validatePositiveNumber
} = require('../utils/validators');

/**
 * Client for Forecasting API
 */
class ForecastingClient {
  /**
   * Create a new ForecastingClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('forecasting');
  }

  /**
   * Get device-level forecast
   * @param {Object} params - Forecast parameters
   * @param {string} params.site_id - Site ID
   * @param {string} params.device_id - Device ID
   * @param {number} [params.forecast_hours=24] - Number of hours to forecast
   * @returns {Promise<Object>} Forecast result
   */
  async getDeviceForecast({ site_id, device_id, forecast_hours = 24 }) {
    validateSiteId(site_id);
    validateDeviceId(device_id);
    validatePositiveNumber(forecast_hours, 'forecast_hours');

    return this.client.post(
      this.endpoint,
      {
        site_id,
        device_id,
        forecast_hours
      },
      { signRequest: true }
    );
  }

  /**
   * Get site-level forecast (aggregated from devices)
   * @param {Object} params - Forecast parameters
   * @param {string} params.site_id - Site ID
   * @param {number} [params.forecast_hours=24] - Number of hours to forecast
   * @param {boolean} [params.include_device_breakdown=false] - Include individual device forecasts
   * @returns {Promise<Object>} Forecast result
   */
  async getSiteForecast({ site_id, forecast_hours = 24, include_device_breakdown = false }) {
    validateSiteId(site_id);
    validatePositiveNumber(forecast_hours, 'forecast_hours');

    return this.client.post(
      this.endpoint,
      {
        site_id,
        forecast_hours,
        include_device_breakdown
      },
      { signRequest: true }
    );
  }

  /**
   * Get customer-level forecast (legacy)
   * @param {Object} params - Forecast parameters
   * @param {string} params.customer_id - Customer ID
   * @param {number} [params.forecast_hours=24] - Number of hours to forecast
   * @returns {Promise<Object>} Forecast result
   */
  async getCustomerForecast({ customer_id, forecast_hours = 24 }) {
    validateCustomerId(customer_id);
    validatePositiveNumber(forecast_hours, 'forecast_hours');

    return this.client.post(
      this.endpoint,
      {
        customer_id,
        forecast_hours
      },
      { signRequest: true }
    );
  }
}

module.exports = ForecastingClient;
