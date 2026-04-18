const { ValidationError } = require('./errors');

class CursorSerializer {
  static serialize(asset_id, timestamp) {
    const payload = JSON.stringify({ asset_id, timestamp });
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
    if (!('asset_id' in data)) {
      throw new ValidationError("Cursor missing required field 'asset_id'", 'cursor', cursor);
    }
    if (!('timestamp' in data)) {
      throw new ValidationError("Cursor missing required field 'timestamp'", 'cursor', cursor);
    }
    if (typeof data.asset_id !== 'string') {
      throw new ValidationError("Cursor 'asset_id' must be a string", 'cursor', cursor);
    }
    if (typeof data.timestamp !== 'string') {
      throw new ValidationError("Cursor 'timestamp' must be a string", 'cursor', cursor);
    }
    return { asset_id: data.asset_id, timestamp: data.timestamp };
  }
}

module.exports = CursorSerializer;
