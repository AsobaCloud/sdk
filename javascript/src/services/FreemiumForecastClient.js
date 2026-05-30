/**
 * Freemium Forecast Client
 *
 * Wraps the public two-step verify+forecast API at forecasting.api.asoba.org.
 * No API key required — first request a verification code, then upload a CSV
 * of historical solar production data and receive a 24-hour energy forecast.
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { ValidationError } = require('../utils/errors');

const FREEMIUM_FORECAST_URL = 'https://forecasting.api.asoba.org/api/v1/freemium-forecast';

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
   * Request a verification code to be sent to the provided email address.
   *
   * @param {Object} params
   * @param {string} params.email - Email address to send the verification code to.
   * @returns {Promise<Object>} Response with message confirming code was sent.
   */
  async requestVerificationCode({ email }) {
    const verifyUrl = `${this._url}/verify`;
    const bodyStr = JSON.stringify({ email });

    return new Promise((resolve, reject) => {
      const url = new URL(verifyUrl);
      const options = {
        hostname: url.hostname,
        port: url.port || (url.protocol === 'https:' ? 443 : 80),
        path: url.pathname,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(bodyStr),
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
          if (res.statusCode >= 500) {
            return reject(new ServiceUnavailableError('Freemium forecast service unavailable'));
          }
          if (res.statusCode !== 200) {
            return reject(new ValidationError(parsed.error || 'Invalid request', 'request', null));
          }
          resolve(parsed);
        });
      });

      req.on('error', (e) => reject(new ServiceUnavailableError(`Request failed: ${e.message}`)));
      req.write(bodyStr);
      req.end();
    });
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
   * @param {string} params.verificationCode - Verification code received via email.
   * @param {number} params.capacityKw - Site capacity in kilowatts.
   * @returns {Promise<Object>} Forecast result with forecasts array and summary.
   *
   * @example
   * const result = await sdk.freemiumForecast.getForecast({
   *   csvPath: './data.csv',
   *   email: 'you@example.com',
   *   siteName: 'My Solar Site',
   *   location: 'Durban',
   *   verificationCode: '123456',
   *   capacityKw: 10.0,
   * });
   * result.forecast.forecasts.forEach(p =>
   *   console.log(`${p.timestamp}: ${p.kWh_forecast} kWh`)
   * );
   */
  async getForecast({ csvPath, email, siteName, location, verificationCode, capacityKw, touAccepted, marketingOptIn }) {
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
    if (!verificationCode) {
      throw new ValidationError('verificationCode is required', 'verificationCode', verificationCode);
    }
    if (capacityKw == null) {
      throw new ValidationError('capacityKw is required', 'capacityKw', capacityKw);
    }
    if (touAccepted !== true) {
      throw new ValidationError('touAccepted must be true to use this service', 'touAccepted', touAccepted);
    }

    const boundary = `----FormBoundary${Date.now().toString(16)}`;
    const filename = path.basename(csvPath);
    const fileContent = fs.readFileSync(csvPath);

    const parts = [
      Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="${filename}"\r\nContent-Type: text/csv\r\n\r\n`),
      fileContent,
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="email"\r\n\r\n${email}`),
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="site_name"\r\n\r\n${siteName}`),
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="location"\r\n\r\n${location}`),
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="verification_code"\r\n\r\n${verificationCode}`),
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="capacity_kw"\r\n\r\n${capacityKw}`),
      Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="tou_accepted"\r\n\r\ntrue`),
    ];

    if (marketingOptIn !== undefined) {
      parts.push(Buffer.from(`\r\n--${boundary}\r\nContent-Disposition: form-data; name="marketing_opt_in"\r\n\r\n${marketingOptIn ? 'true' : 'false'}`));
    }

    parts.push(Buffer.from(`\r\n--${boundary}--\r\n`));

    const body = Buffer.concat(parts);

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