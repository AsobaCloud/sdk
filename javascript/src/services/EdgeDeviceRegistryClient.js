/**
 * Edge Device Registry Client
 * Manages edge device discovery, registration, and capability detection
 */

const { validateRequired, validateString } = require('../utils/validators');

/**
 * Client for Edge Device Registry Service
 */
class EdgeDeviceRegistryClient {
  /**
   * Create a new EdgeDeviceRegistryClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('edgeRegistry');
  }

  /**
   * Get all registered devices
   * @returns {Promise<Array>} List of devices
   */
  async getDevices() {
    return this.client.get(`${this.endpoint}/api/devices`);
  }

  /**
   * Get a specific device
   * @param {string} deviceId - Device ID
   * @returns {Promise<Object>} Device details
   */
  async getDevice(deviceId) {
    validateString(deviceId, 'deviceId');

    return this.client.get(`${this.endpoint}/api/devices/${deviceId}`);
  }

  /**
   * Discover and register a new device
   * @param {Object} params - Device parameters
   * @param {string} params.ip - Device IP address
   * @param {string} params.username - SSH username for device
   * @returns {Promise<Object>} Registered device
   */
  async discoverDevice({ ip, username }) {
    validateRequired({ ip, username }, ['ip', 'username']);

    return this.client.post(`${this.endpoint}/api/devices`, {
      ip,
      username
    });
  }

  /**
   * Update device information
   * @param {string} deviceId - Device ID
   * @param {Object} updates - Updates to apply
   * @returns {Promise<Object>} Updated device
   */
  async updateDevice(deviceId, updates) {
    validateString(deviceId, 'deviceId');
    validateRequired({ updates }, ['updates']);

    return this.client.put(`${this.endpoint}/api/devices/${deviceId}`, updates);
  }

  /**
   * Delete a device from registry
   * @param {string} deviceId - Device ID
   * @returns {Promise<Object>} Deletion confirmation
   */
  async deleteDevice(deviceId) {
    validateString(deviceId, 'deviceId');

    return this.client.delete(`${this.endpoint}/api/devices/${deviceId}`);
  }

  /**
   * Get device capabilities
   * @param {string} deviceId - Device ID
   * @returns {Promise<Object>} Device capabilities
   */
  async getDeviceCapabilities(deviceId) {
    validateString(deviceId, 'deviceId');

    return this.client.get(`${this.endpoint}/api/devices/${deviceId}/capabilities`);
  }

  /**
   * Get device services
   * @param {string} deviceId - Device ID
   * @returns {Promise<Array>} List of services running on device
   */
  async getDeviceServices(deviceId) {
    validateString(deviceId, 'deviceId');

    return this.client.get(`${this.endpoint}/api/devices/${deviceId}/services`);
  }

  /**
   * Get service health status
   * @returns {Promise<Object>} Health status
   */
  async getHealth() {
    return this.client.get(`${this.endpoint}/health`);
  }
}

module.exports = EdgeDeviceRegistryClient;
