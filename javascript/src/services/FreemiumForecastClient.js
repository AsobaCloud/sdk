/**
 * Freemium Forecast Client
 *
 * Wraps the public POST https://api.asoba.co/v1/freemium-forecast endpoint.
 * No API key required — upload a CSV of historical solar production data
 * and receive a 24-hour energy forecast.
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { ValidationError } = require('../utils/errors');

const FREEMIUM_FORECAST_URL = 'https://api.asoba.co/v1/freemium-forecast';

class ServiceUnavailableError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ServiceUnavailableError';
    this.code = 'SERVICE_UNAVAILABLE';
  }
}

class FreemiumForecastClient {
  constructor(_config) {
    this._url = FREEMIUM_FORECAST_URL;
  }

  /**
   * Generate a 24-hour solar energy forecast from a CSV file.
   *
   * @param {Object} params
   * @param {string} params.csvPath - Path to CSV file with historical solar production data.
   *   Must contain a timestamp column and a power/energy column.
   * @param {string} params.email - Your email address (used to identify requests).
   * @param {string} params.siteName - Descriptive name for the solar site.
   * @param {string} params.location - General location of the site (e.g. "Durban").
   * @returns {Promise<Object>} Forecast result with forecasts array and summary.
   *
   * @example
   * const result = await sdk.freemiumForecast.getForecast({
   *   csvPath: './data.csv',
   *   email: 'you@example.com',
   *   siteName: 'My Solar Site',
   *   location: 'Durban',
   * });
   * result.forecast.forecasts.forEach(p =>
   *   console.log(`${p.timestamp}: ${p.kWh_forecast} kWh`)
   * );
   */
  async getForecast({ csvPath, email, siteName, location }) {
    if (!csvPath || !fs.existsSync(csvPath)) {
      throw new ValidationError(`CSV file not found: ${csvPath}`, 'csvPath', csvPath);
    }
    if (!email || !email.includes('@')) {
      throw new ValidationError(`Invalid email address: ${email}`, 'email', email);
    }
    if (!siteName) {
      throw new ValidationError('siteName is required', 'siteName', siteName);
    }
    if (!location) {
      throw new ValidationError('location is required', 'location', location);
    }

    const boundary = `----FormBoundary${Date.now().toString(16)}`;
    const filename = path.basename(csvPath);
    const fileContent = fs.readFileSync(csvPath);

    const body = Buffer.concat([
      Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${filename}"\r\nContent-Type: text/csv\r\n\r\n`),
      fileContent,
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="email"\r\n\r\n${email}`),
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="site_name"\r\n\r\n${siteName}`),
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="location"\r\n\r\n${location}`),
      Buffer.from(`\r\n--${boundary}--\r\n`),
    ]);

    return new Promise((resolve, reject) => {
      const url = new URL(this._url);
      const options = {
        hostname: url.hostname,
        port: url.port || 443,
        path: url.pathname,
        method: 'POST',
        headers: {
          'Content-Type': `multipart/form-data; boundary=${boundary}`,
          'Content-Length': body.length,
        },
      };

      const transport = url.protocol === 'https:' ? https : http;
      const req = transport.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          let parsed;
          try { parsed = JSON.parse(data); } catch (e) {
            return reject(new ServiceUnavailableError(`Invalid JSON response: ${e.message}`));
          }
          if (res.statusCode === 400) {
            return reject(new ValidationError(parsed.error || 'Invalid request', 'request', null));
          }
          if (res.statusCode >= 500) {
            return reject(new ServiceUnavailableError('Freemium forecast service unavailable'));
          }
          if (res.statusCode !== 200) {
            return reject(new ServiceUnavailableError(`Unexpected status ${res.statusCode}`));
          }
          resolve(parsed);
        });
      });

      req.on('error', (e) => reject(new ServiceUnavailableError(`Request failed: ${e.message}`)));
      req.write(body);
      req.end();
    });
  }
}

module.exports = { FreemiumForecastClient, ServiceUnavailableError };