const { ValidationError } = require('./errors');

class OodaCursorSerializer {
  static serialize(terminal_device_id, timestamp) {
    const payload = JSON.stringify({ terminal_device_id, timestamp });
    return Buffer.from(payload).toString('base64url');
  }

  static deserialize(cursor) {
    let data;
    try {
      const json = Buffer.from(cursor, 'base64url').toString('utf8');
      data = JSON.parse(json);
    } catch (e) {
      throw new ValidationError(`Cursor is malformed: ${e.message}`, 'cursor', cursor);
    }
    if (typeof data !== 'object' || data === null) {
      throw new ValidationError('Cursor must decode to a JSON object', 'cursor', cursor);
    }
    if (!('terminal_device_id' in data)) {
      throw new ValidationError("Cursor missing required field 'terminal_device_id'", 'cursor', cursor);
    }
    if (!('timestamp' in data)) {
      throw new ValidationError("Cursor missing required field 'timestamp'", 'cursor', cursor);
    }
    if (typeof data.terminal_device_id !== 'string') {
      throw new ValidationError("Cursor 'terminal_device_id' must be a string", 'cursor', cursor);
    }
    if (typeof data.timestamp !== 'string') {
      throw new ValidationError("Cursor 'timestamp' must be a string", 'cursor', cursor);
    }
    return { terminal_device_id: data.terminal_device_id, timestamp: data.timestamp };
  }
}

module.exports = OodaCursorSerializer;