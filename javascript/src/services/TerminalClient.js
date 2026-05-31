/**
 * Terminal API Client
 * Provides OODA workflow operations (Observe, Orient, Decide, Act)
 */

const {
  validateRequired,
  validateCustomerId,
  validateAssetId
} = require('../utils/validators');

/**
 * Client for Terminal API (OODA workflow)
 */
class TerminalClient {
  /**
   * Create a new TerminalClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('terminal');
  }

  /**
   * List all assets for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of assets. Battery assets include capacity_kwh,
   * warranty_expiry_date, and warranty_throughput_kwh fields.
   */
  async listAssets({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/assets`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * Add a new asset
   * @param {Object} params - Asset parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} params.asset_id - Asset ID
   * @param {string} params.name - Asset name
   * @param {string} params.type - Asset type
   * @param {number} params.capacity_kw - Asset capacity in kW
   * @param {string} params.location - Asset location
   * @param {string} [params.timezone='Africa/Johannesburg'] - Asset timezone
   * @param {Array} [params.components=[]] - Asset components
   * @param {number} [params.capacity_kwh] - Optional battery capacity in kWh
   * @param {string} [params.warranty_expiry_date] - Optional warranty expiry date (YYYY-MM-DD)
   * @param {number} [params.warranty_throughput_kwh] - Optional warranty throughput limit in kWh
   * @returns {Promise<Object>} Created asset
   */
  async addAsset(params) {
    validateRequired(params, ['customer_id', 'asset_id', 'name', 'type', 'capacity_kw', 'location']);

    return this.client.post(
      `${this.endpoint}/assets`,
      {
        action: 'add',
        ...params
      },
      { signRequest: true }
    );
  }

  /**
   * Get a specific asset
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} params.asset_id - Asset ID
   * @returns {Promise<Object|null>} Asset details or null if not found
   */
  async getAsset({ customer_id, asset_id }) {
    validateCustomerId(customer_id);
    validateAssetId(asset_id);

    try {
      return await this.client.post(
        `${this.endpoint}/assets`,
        {
          action: 'get',
          customer_id,
          asset_id
        },
        { signRequest: true }
      );
    } catch (error) {
      if (error.statusCode === 404) {
        return null;
      }
      throw error;
    }
  }

  /**
   * Calculate remaining warranty life for a battery asset.
   *
   * @param {Object} params - Parameters
   * @param {string} [params.warranty_expiry_date] - Warranty expiry date in ISO format (YYYY-MM-DD)
   * @param {number} [params.warranty_throughput_kwh] - Total warranty throughput limit in kWh
   * @param {number} [params.current_throughput_kwh] - Current cumulative throughput in kWh
   * @returns {Object} Warranty life information with keys:
   * - days_remaining: Days until date-based warranty expiry (null if no date)
   * - throughput_remaining_pct: Percentage of throughput warranty remaining (null if no limit)
   * - warranty_status: 'in_warranty', 'expiring_soon', 'out_of_warranty', or 'unknown'
   * - limiting_factor: 'date' or 'throughput' indicating which constraint is tighter
   */
  static calculateRemainingWarrantyLife({
    warranty_expiry_date,
    warranty_throughput_kwh,
    current_throughput_kwh,
  }) {
    // Use UTC for consistent date math across timezones
    const now = new Date();
    const today = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));

    let days_remaining = null;
    let throughput_remaining_pct = null;
    let warranty_status = 'unknown';
    let limiting_factor = null;
    let date_status = 'unknown';
    let throughput_status = 'unknown';

    // Check date-based warranty
    if (warranty_expiry_date) {
      // Parse YYYY-MM-DD as UTC
      const [year, month, day] = warranty_expiry_date.split('-').map(Number);
      const expiry = new Date(Date.UTC(year, month - 1, day));
      
      if (!isNaN(expiry.getTime())) {
        days_remaining = Math.round((expiry - today) / (1000 * 60 * 60 * 24));
        if (days_remaining < 0) {
          date_status = 'out_of_warranty';
        } else if (days_remaining < 90) {
          date_status = 'expiring_soon';
        } else {
          date_status = 'in_warranty';
        }
      }
    }

    // Check throughput-based warranty
    if (warranty_throughput_kwh && current_throughput_kwh !== undefined && current_throughput_kwh !== null) {
      if (warranty_throughput_kwh > 0) {
        const throughput_remaining = Math.max(0, warranty_throughput_kwh - current_throughput_kwh);
        throughput_remaining_pct = (throughput_remaining / warranty_throughput_kwh) * 100;
        if (current_throughput_kwh >= warranty_throughput_kwh) {
          throughput_status = 'out_of_warranty';
        } else if (current_throughput_kwh >= warranty_throughput_kwh * 0.8) {
          throughput_status = 'expiring_soon';
        } else {
          throughput_status = 'in_warranty';
        }
      }
    }

    // Determine overall warranty status (worst of the two)
    if (date_status === 'out_of_warranty' || throughput_status === 'out_of_warranty') {
      warranty_status = 'out_of_warranty';
    } else if (date_status === 'expiring_soon' || throughput_status === 'expiring_soon') {
      warranty_status = 'expiring_soon';
    } else if (date_status === 'in_warranty' || throughput_status === 'in_warranty') {
      warranty_status = 'in_warranty';
    }

    // Determine limiting factor
    if (days_remaining !== null && throughput_remaining_pct !== null) {
      if (throughput_remaining_pct < 20) {
        limiting_factor = 'throughput';
      } else if (days_remaining < 90) {
        limiting_factor = 'date';
      } else {
        limiting_factor = 'date';
      }
    } else if (days_remaining !== null) {
      limiting_factor = 'date';
    } else if (throughput_remaining_pct !== null) {
      limiting_factor = 'throughput';
    }

    return {
      days_remaining,
      throughput_remaining_pct: throughput_remaining_pct !== null ? Math.round(throughput_remaining_pct * 10) / 10 : null,
      warranty_status,
      limiting_factor,
    };
  }

  /**
   * Run fault detection on an asset (Observe phase)
   * @param {Object} params - Detection parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} params.asset_id - Asset ID
   * @param {number} [params.lookback_hours=6] - Hours of data to analyze
   * @returns {Promise<Object>} Detection results
   */
  async runDetection({ customer_id, asset_id, lookback_hours = 6 }) {
    validateCustomerId(customer_id);
    validateAssetId(asset_id);

    return this.client.post(
      `${this.endpoint}/detect`,
      {
        action: 'run',
        customer_id,
        asset_id,
        lookback_hours
      },
      { signRequest: true }
    );
  }

  /**
   * List detections for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of detections
   */
  async listDetections({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/detect`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * Run diagnostics on a detected fault (Orient phase)
   * @param {Object} params - Diagnostic parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} params.asset_id - Asset ID
   * @param {string} params.detection_id - Detection ID
   * @param {number} [params.lookback_hours=6] - Hours of data to analyze
   * @returns {Promise<Object>} Diagnostic results
   */
  async runDiagnostics({ customer_id, asset_id, detection_id, lookback_hours = 6 }) {
    validateRequired({ customer_id, asset_id, detection_id }, ['customer_id', 'asset_id', 'detection_id']);

    return this.client.post(
      `${this.endpoint}/diagnose`,
      {
        action: 'run',
        customer_id,
        asset_id,
        detection_id,
        lookback_hours
      },
      { signRequest: true }
    );
  }

  /**
   * List diagnostics for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of diagnostics
   */
  async listDiagnostics({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/diagnose`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * Create a maintenance schedule (Decide phase)
   * @param {Object} params - Schedule parameters
   * @param {string} params.customer_id - Customer ID
   * @param {Object} scheduleData - Schedule data
   * @returns {Promise<Object>} Created schedule
   */
  async createSchedule({ customer_id, ...scheduleData }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/schedule`,
      {
        action: 'create',
        customer_id,
        ...scheduleData
      },
      { signRequest: true }
    );
  }

  /**
   * List maintenance schedules for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of schedules
   */
  async listSchedules({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/schedule`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * Build a Bill of Materials (Act phase)
   * @param {Object} params - BOM parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} params.asset_id - Asset ID
   * @param {string} [params.schedule_id] - Schedule ID
   * @returns {Promise<Object>} BOM details
   */
  async buildBOM({ customer_id, asset_id, schedule_id }) {
    validateCustomerId(customer_id);
    validateAssetId(asset_id);

    return this.client.post(
      `${this.endpoint}/bom`,
      {
        action: 'build',
        customer_id,
        asset_id,
        schedule_id
      },
      { signRequest: true }
    );
  }

  /**
   * List BOMs for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of BOMs
   */
  async listBOMs({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/bom`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * Create a work order (Act phase)
   * @param {Object} params - Order parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} params.asset_id - Asset ID
   * @param {string} [params.bom_id] - BOM ID
   * @returns {Promise<Object>} Created order
   */
  async createOrder({ customer_id, asset_id, bom_id }) {
    validateCustomerId(customer_id);
    validateAssetId(asset_id);

    return this.client.post(
      `${this.endpoint}/order`,
      {
        action: 'create',
        customer_id,
        asset_id,
        bom_id
      },
      { signRequest: true }
    );
  }

  /**
   * List orders for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of orders
   */
  async listOrders({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/order`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * Subscribe to job tracking
   * @param {Object} params - Tracking parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} params.job_id - Job ID
   * @returns {Promise<Object>} Tracking subscription
   */
  async subscribeTracking({ customer_id, job_id }) {
    validateRequired({ customer_id, job_id }, ['customer_id', 'job_id']);

    return this.client.post(
      `${this.endpoint}/track`,
      {
        action: 'subscribe',
        customer_id,
        job_id
      },
      { signRequest: true }
    );
  }

  /**
   * List tracking subscriptions for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of tracking subscriptions
   */
  async listTracking({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/track`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * List activities across all OODA phases
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of activities
   */
  async listActivities({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/activities`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * List issues for a customer
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} List of issues
   */
  async listIssues({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/issues`,
      {
        action: 'list',
        customer_id
      },
      { signRequest: true }
    );
  }

  /**
   * Create a new issue
   * @param {Object} params - Issue parameters
   * @param {string} params.customer_id - Customer ID
   * @param {Object} issueData - Issue data
   * @returns {Promise<Object>} Created issue
   */
  async createIssue({ customer_id, ...issueData }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/issues`,
      {
        action: 'create',
        customer_id,
        ...issueData
      },
      { signRequest: true }
    );
  }

  /**
   * Get high-level site summary with KPIs and asset intelligence data.
   * Includes fleet PR, availability, and intelligence sections (battery, soiling, prognostics) if available.
   * @param {Object} params - Parameters
   * @param {string} params.site_id - Site or customer identifier
   * @returns {Promise<Object>} Site summary data
   */
  async getSiteSummary({ site_id }) {
    if (!site_id) throw new Error('site_id is required');

    return this.client.post(
      `${this.endpoint}/telemetry`,
      {
        action: 'site-summary',
        site_id
      },
      { signRequest: true }
    );
  }

  /**
   * Get nowcast UI data for monitoring dashboard
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @param {string} [params.time_range='1h'] - Time range (1h, 6h, 24h, 7d, latest)
   * @param {Array<string>} [params.asset_filter=[]] - Filter by specific assets
   * @returns {Promise<Object>} Nowcast data
   */
  async getNowcastData({ customer_id, time_range = '1h', asset_filter = [] }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/nowcastUI`,
      {
        action: 'list',
        customer_id,
        time_range,
        asset_filter
      },
      { signRequest: true }
    );
  }

  /**
   * Get forecast results
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} Forecast results
   */
  async getForecastResults({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/forecast`,
      { customer_id },
      { signRequest: true }
    );
  }

  /**
   * Get interpolation results
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} Interpolation results
   */
  async getInterpolationResults({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/interpolation`,
      { customer_id },
      { signRequest: true }
    );
  }

  /**
   * Get ML model registry
   * @returns {Promise<Object>} Model registry
   */
  async getMLModels() {
    return this.client.post(
      `${this.endpoint}/ml-models`,
      {},
      { signRequest: true }
    );
  }

  /**
   * Get ML-enhanced OODA data
   * @param {Object} params - Parameters
   * @param {string} params.customer_id - Customer ID
   * @returns {Promise<Object>} ML-enhanced activities
   */
  async getMLOODA({ customer_id }) {
    validateCustomerId(customer_id);

    return this.client.post(
      `${this.endpoint}/ooda`,
      { customer_id },
      { signRequest: true }
    );
  }
}

module.exports = TerminalClient;
