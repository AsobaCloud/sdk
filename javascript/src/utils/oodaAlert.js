const { ValidationError } = require('./errors');

const REQUIRED_FIELDS = ['terminal_device_id', 'site_id', 'timestamp', 'alert_type', 'alert_severity', 'message', 'source_system', 'resolved'];
const OPTIONAL_FIELDS = ['terminal_ts', 'metadata'];
const STRIP_FIELDS = new Set(['expires_at']);

function parseOodaAlert(data) {
  for (const field of REQUIRED_FIELDS) {
    if (!(field in data)) {
      throw new ValidationError(
        `OodaAlert missing required field: '${field}'`,
        field,
        undefined
      );
    }
  }
  const alert = {};
  for (const field of REQUIRED_FIELDS) {
    alert[field] = data[field];
  }
  for (const field of OPTIONAL_FIELDS) {
    alert[field] = field in data ? data[field] : null;
  }
  // Strip internal fields
  for (const field of STRIP_FIELDS) {
    delete alert[field];
  }
  alert.cursor = data.cursor || null;
  return alert;
}

module.exports = { parseOodaAlert, REQUIRED_FIELDS, OPTIONAL_FIELDS };