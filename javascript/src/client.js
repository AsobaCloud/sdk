/**
 * HTTP Client wrapper with retry logic and AWS signing
 */

const axios = require('axios');
const aws4 = require('aws4');
const { APIError, TimeoutError, AuthenticationError } = require('./utils/errors');

/**
 * Base HTTP client for making API requests
 */
class HTTPClient {
  /**
   * Create a new HTTP client
   * @param {Config} config - SDK configuration
   */
  constructor(config) {
    this.config = config;
    this.axios = axios.create({
      timeout: config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': '@asoba/ona-sdk/1.0.0'
      }
    });
  }

  /**
   * Make a request with automatic retries
   * @param {Object} options - Request options
   * @param {string} options.method - HTTP method
   * @param {string} options.url - Request URL
   * @param {Object} [options.data] - Request body
   * @param {Object} [options.headers] - Additional headers
   * @param {boolean} [options.signRequest] - Whether to sign request with AWS credentials
   * @param {number} [attempt=1] - Current attempt number
   * @returns {Promise<Object>} Response data
   */
  async request(options, attempt = 1) {
    try {
      const requestConfig = {
        method: options.method,
        url: options.url,
        headers: { ...options.headers }
      };

      // Add request body if present
      if (options.data) {
        requestConfig.data = options.data;
      }

      // Sign request if AWS credentials are available and signRequest is true
      if (options.signRequest && this.config.hasCredentials()) {
        this.signRequest(requestConfig);
      }

      // Make the request
      const response = await this.axios.request(requestConfig);

      return response.data;
    } catch (error) {
      // Handle timeout errors
      if (error.code === 'ECONNABORTED') {
        throw new TimeoutError(
          `Request timed out after ${this.config.timeout}ms`,
          this.config.timeout
        );
      }

      // Handle authentication errors
      if (error.response && error.response.status === 401) {
        throw new AuthenticationError(
          error.response.data?.error || 'Authentication failed'
        );
      }

      // Handle API errors
      if (error.response) {
        const statusCode = error.response.status;
        const message = error.response.data?.error || error.message;

        // Retry on server errors and rate limiting
        if ((statusCode >= 500 || statusCode === 429) && attempt < this.config.retries) {
          await this.delay(this.config.retryDelay * attempt);
          return this.request(options, attempt + 1);
        }

        throw new APIError(message, statusCode, error.response.data);
      }

      // Retry on network errors
      if (attempt < this.config.retries) {
        await this.delay(this.config.retryDelay * attempt);
        return this.request(options, attempt + 1);
      }

      // Re-throw unknown errors
      throw error;
    }
  }

  /**
   * Sign request with AWS Signature v4
   * @param {Object} requestConfig - Request configuration
   */
  signRequest(requestConfig) {
    const credentials = this.config.getCredentials();

    if (!credentials) {
      return;
    }

    const urlObj = new URL(requestConfig.url);

    const opts = {
      host: urlObj.host,
      path: urlObj.pathname + urlObj.search,
      method: requestConfig.method,
      headers: requestConfig.headers,
      body: requestConfig.data ? JSON.stringify(requestConfig.data) : undefined,
      region: this.config.region,
      service: 'lambda'
    };

    aws4.sign(opts, {
      accessKeyId: credentials.accessKeyId,
      secretAccessKey: credentials.secretAccessKey,
      sessionToken: credentials.sessionToken
    });

    // Apply signed headers
    requestConfig.headers = opts.headers;
  }

  /**
   * Make a GET request
   * @param {string} url - Request URL
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>} Response data
   */
  async get(url, options = {}) {
    return this.request({
      method: 'GET',
      url,
      ...options
    });
  }

  /**
   * Make a POST request
   * @param {string} url - Request URL
   * @param {Object} data - Request body
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>} Response data
   */
  async post(url, data, options = {}) {
    return this.request({
      method: 'POST',
      url,
      data,
      ...options
    });
  }

  /**
   * Make a PUT request
   * @param {string} url - Request URL
   * @param {Object} data - Request body
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>} Response data
   */
  async put(url, data, options = {}) {
    return this.request({
      method: 'PUT',
      url,
      data,
      ...options
    });
  }

  /**
   * Make a DELETE request
   * @param {string} url - Request URL
   * @param {Object} [options] - Request options
   * @returns {Promise<Object>} Response data
   */
  async delete(url, options = {}) {
    return this.request({
      method: 'DELETE',
      url,
      ...options
    });
  }

  /**
   * Delay execution for specified milliseconds
   * @param {number} ms - Milliseconds to delay
   * @returns {Promise<void>}
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = HTTPClient;
