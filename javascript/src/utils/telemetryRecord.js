const { ValidationError } = require('./errors');

const REQUIRED_FIELDS = ['asset_id', 'site_id', 'timestamp', 'power', 'kWh', 'inverter_state', 'run_state'];
const OPTIONAL_FIELDS = ['asset_ts', 'kVArh', 'kVA', 'PF', 'temperature', 'error_code', 'error_type'];
const STRIP_FIELDS = new Set(['expires_at']);

function parseTelemetryRecord(data) {
  for (const field of REQUIRED_FIELDS) {
    if (!(field in data)) {
      throw new ValidationError(
        `TelemetryRecord missing required field: '${field}'`,
        field,
        undefined
      );
    }
  }
  const record = {};
  for (const field of REQUIRED_FIELDS) {
    record[field] = data[field];
  }
  for (const field of OPTIONAL_FIELDS) {
    record[field] = field in data ? data[field] : null;
  }
  // Strip internal fields
  for (const field of STRIP_FIELDS) {
    delete record[field];
  }
  record.cursor = data.cursor || null;
  return record;
}

module.exports = { parseTelemetryRecord, REQUIRED_FIELDS, OPTIONAL_FIELDS };
