const https = require('https');
const http = require('http');
const { URL } = require('url');
const { ConfigurationError, ValidationError, AuthenticationError, APIError } = require('../utils/errors');
const CursorSerializer = require('../utils/cursorSerializer');
const { parseTelemetryRecord } = require('../utils/telemetryRecord');

const MAX_LIMIT = 1000;
const MAX_DAYS_MS = 31 * 24 * 60 * 60 * 1000;
const MIN_POLLING_INTERVAL = 5;

class RateLimitError extends Error {
  constructor(message) {
    super(message);
    this.name = 'RateLimitError';
    this.code = 'RATE_LIMIT_ERROR';
  }
}

class ServiceUnavailableError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ServiceUnavailableError';
    this.code = 'SERVICE_UNAVAILABLE';
  }
}

class InverterTelemetryClient {
  constructor(config) {
    const endpoint = (config.endpoints && config.endpoints.inverterTelemetry) || null;
    const apiKey = config.inverterTelemetryApiKey || null;

    if (!endpoint) {
      throw new ConfigurationError('inverterTelemetry endpoint is required', ['endpoints.inverterTelemetry']);
    }
    if (!endpoint.startsWith('https://')) {
      throw new ConfigurationError('inverterTelemetry endpoint must use https://', ['endpoints.inverterTelemetry']);
    }
    if (!apiKey) {
      throw new AuthenticationError('inverterTelemetryApiKey is required');
    }

    this._endpoint = endpoint.replace(/\/$/, '');
    this._apiKey = apiKey;
    this._pollingInterval = config.telemetryPollingInterval !== undefined ? config.telemetryPollingInterval : 5;
    this._retries = config.retries !== undefined ? config.retries : 3;
    this._activeStreams = new Set();
  }

  _validateQueryParams(site_id, time_range, limit) {
    if (!site_id) throw new ValidationError('site_id is required', 'site_id', site_id);
    if (time_range.start > time_range.end) {
      throw new ValidationError('time_range.start must be <= time_range.end', 'time_range', time_range);
    }
    if (limit > MAX_LIMIT) {
      throw new ValidationError(`limit must not exceed ${MAX_LIMIT}`, 'limit', limit);
    }
    const spanMs = new Date(time_range.end) - new Date(time_range.start);
    if (spanMs > MAX_DAYS_MS) {
      throw new ValidationError(`time_range span must not exceed 31 days`, 'time_range', time_range);
    }
  }

  _request(path, params) {
    return new Promise((resolve, reject) => {
      const url = new URL(this._endpoint + path);
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
      }
      const options = {
        hostname: url.hostname,
        port: url.port || 443,
        path: url.pathname + url.search,
        method: 'GET',
        headers: {
          'x-api-key': this._apiKey,
          'Accept': 'application/json',
        },
      };
      // Use http module for http:// (tests use local http server)
      const transport = url.protocol === 'https:' ? https : http;
      const req = transport.request(options, (res) => {
        let body = '';
        res.on('data', chunk => body += chunk);
        res.on('end', () => {
          if (res.statusCode === 401 || res.statusCode === 403) {
            return reject(new AuthenticationError(`HTTP ${res.statusCode}: Access denied`));
          }
          if (res.statusCode === 429) {
            return reject(new RateLimitError('Rate limit exceeded'));
          }
          if (res.statusCode >= 500) {
            return reject(new ServiceUnavailableError(`HTTP ${res.statusCode}`));
          }
          if (res.statusCode >= 400) {
            return reject(new ValidationError(`HTTP ${res.statusCode}: ${body}`, 'request', null));
          }
          try {
            resolve(JSON.parse(body));
          } catch (e) {
            reject(new Error(`Invalid JSON response: ${e.message}`));
          }
        });
      });
      req.on('error', reject);
      req.end();
    });
  }

  async _requestWithRetry(path, params) {
    let lastErr;
    for (let attempt = 0; attempt <= this._retries; attempt++) {
      try {
        return await this._request(path, params);
      } catch (err) {
        if (err instanceof AuthenticationError || err instanceof RateLimitError || err instanceof ValidationError) {
          throw err;
        }
        lastErr = err;
        if (attempt < this._retries) {
          await new Promise(r => setTimeout(r, Math.pow(2, attempt) * 100));
        }
      }
    }
    throw new ServiceUnavailableError(`Service unavailable after ${this._retries} retries: ${lastErr?.message}`);
  }

  async getInverterTelemetry({ asset_id, site_id, time_range, resolution = '5min', limit = 100, cursor } = {}) {
    this._validateQueryParams(site_id, time_range, limit);
    const params = { asset_id, site_id, start: time_range.start, end: time_range.end, resolution, limit };
    if (cursor) params.cursor = cursor;
    const data = await this._requestWithRetry('/telemetry/inverter', params);
    return (data.records || []).map(parseTelemetryRecord);
  }

  async getSiteTelemetry({ site_id, time_range, resolution = '5min', limit = 100 } = {}) {
    this._validateQueryParams(site_id, time_range, limit);
    const params = { site_id, start: time_range.start, end: time_range.end, resolution, limit };
    const data = await this._requestWithRetry('/telemetry/site', params);
    const result = {};
    for (const [aid, records] of Object.entries(data.records || {})) {
      result[aid] = records.map(parseTelemetryRecord);
    }
    return result;
  }

  async* streamInverter({ asset_id, site_id, cursor, polling_interval } = {}) {
    const interval = polling_interval !== undefined ? polling_interval : this._pollingInterval;
    if (interval < MIN_POLLING_INTERVAL) {
      throw new ValidationError(`polling_interval must be >= ${MIN_POLLING_INTERVAL}`, 'polling_interval', interval);
    }
    const streamKey = `inverter:${asset_id}`;
    if (this._activeStreams.has(streamKey)) {
      throw new ValidationError(`Stream already active for asset_id=${asset_id}`, 'asset_id', asset_id);
    }
    this._activeStreams.add(streamKey);
    let lastTs = null;
    if (cursor) {
      const obj = CursorSerializer.deserialize(cursor);
      lastTs = obj.timestamp;
    }
    try {
      while (true) {
        const params = {
          asset_id, site_id,
          start: lastTs || '1970-01-01T00:00:00',
          end: '9999-12-31T23:59:59',
          resolution: '5min', limit: MAX_LIMIT,
        };
        const data = await this._requestWithRetry('/telemetry/inverter', params);
        for (const r of (data.records || [])) {
          const record = parseTelemetryRecord(r);
          if (lastTs === null || record.timestamp > lastTs) {
            lastTs = record.timestamp;
            record.cursor = CursorSerializer.serialize(asset_id, lastTs);
            yield record;
          }
        }
        await new Promise(r => setTimeout(r, interval * 1000));
      }
    } finally {
      this._activeStreams.delete(streamKey);
    }
  }

  async* streamSite({ site_id, cursor, polling_interval } = {}) {
    const interval = polling_interval !== undefined ? polling_interval : this._pollingInterval;
    if (interval < MIN_POLLING_INTERVAL) {
      throw new ValidationError(`polling_interval must be >= ${MIN_POLLING_INTERVAL}`, 'polling_interval', interval);
    }
    const streamKey = `site:${site_id}`;
    if (this._activeStreams.has(streamKey)) {
      throw new ValidationError(`Stream already active for site_id=${site_id}`, 'site_id', site_id);
    }
    this._activeStreams.add(streamKey);
    const lastTsMap = {};
    if (cursor) {
      const obj = CursorSerializer.deserialize(cursor);
      lastTsMap[obj.asset_id] = obj.timestamp;
    }
    try {
      while (true) {
        const minTs = Object.values(lastTsMap).length > 0
          ? Object.values(lastTsMap).sort()[0]
          : '1970-01-01T00:00:00';
        const params = { site_id, start: minTs, end: '9999-12-31T23:59:59', resolution: '5min', limit: MAX_LIMIT };
        const data = await this._requestWithRetry('/telemetry/site', params);
        const allRecords = [];
        for (const [aid, recs] of Object.entries(data.records || {})) {
          for (const r of recs) {
            const record = parseTelemetryRecord(r);
            const prev = lastTsMap[aid];
            if (!prev || record.timestamp > prev) allRecords.push(record);
          }
        }
        allRecords.sort((a, b) => a.timestamp < b.timestamp ? -1 : 1);
        for (const record of allRecords) {
          lastTsMap[record.asset_id] = record.timestamp;
          record.cursor = CursorSerializer.serialize(record.asset_id, record.timestamp);
          yield record;
        }
        await new Promise(r => setTimeout(r, interval * 1000));
      }
    } finally {
      this._activeStreams.delete(streamKey);
    }
  }
  async getDataPeriod({ site_id, asset_id } = {}) {
    if (!site_id) throw new ValidationError('site_id is required', 'site_id', site_id);
    const params = { site_id };
    if (asset_id) params.asset_id = asset_id;
    return this._requestWithRetry('/telemetry/data-period', params);
  }
}

module.exports = { InverterTelemetryClient, RateLimitError, ServiceUnavailableError };
