/**
 * Input validation utilities
 */

const { ValidationError } = require('./errors');

/**
 * Validate required fields in an object
 * @param {Object} obj - Object to validate
 * @param {string[]} requiredFields - Array of required field names
 * @throws {ValidationError} If any required field is missing
 */
function validateRequired(obj, requiredFields) {
  const missing = [];

  for (const field of requiredFields) {
    if (obj[field] === undefined || obj[field] === null || obj[field] === '') {
      missing.push(field);
    }
  }

  if (missing.length > 0) {
    throw new ValidationError(
      `Missing required fields: ${missing.join(', ')}`,
      missing[0],
      undefined
    );
  }
}

/**
 * Validate that a value is a string
 * @param {*} value - Value to validate
 * @param {string} fieldName - Name of the field
 * @throws {ValidationError} If value is not a string
 */
function validateString(value, fieldName) {
  if (typeof value !== 'string') {
    throw new ValidationError(
      `${fieldName} must be a string`,
      fieldName,
      value
    );
  }
}

/**
 * Validate that a value is a number
 * @param {*} value - Value to validate
 * @param {string} fieldName - Name of the field
 * @throws {ValidationError} If value is not a number
 */
function validateNumber(value, fieldName) {
  if (typeof value !== 'number' || isNaN(value)) {
    throw new ValidationError(
      `${fieldName} must be a number`,
      fieldName,
      value
    );
  }
}

/**
 * Validate that a value is a positive number
 * @param {*} value - Value to validate
 * @param {string} fieldName - Name of the field
 * @throws {ValidationError} If value is not a positive number
 */
function validatePositiveNumber(value, fieldName) {
  validateNumber(value, fieldName);
  if (value <= 0) {
    throw new ValidationError(
      `${fieldName} must be a positive number`,
      fieldName,
      value
    );
  }
}

/**
 * Validate that a value is within a range
 * @param {number} value - Value to validate
 * @param {string} fieldName - Name of the field
 * @param {number} min - Minimum value (inclusive)
 * @param {number} max - Maximum value (inclusive)
 * @throws {ValidationError} If value is out of range
 */
function validateRange(value, fieldName, min, max) {
  validateNumber(value, fieldName);
  if (value < min || value > max) {
    throw new ValidationError(
      `${fieldName} must be between ${min} and ${max}`,
      fieldName,
      value
    );
  }
}

/**
 * Validate that a value is an array
 * @param {*} value - Value to validate
 * @param {string} fieldName - Name of the field
 * @throws {ValidationError} If value is not an array
 */
function validateArray(value, fieldName) {
  if (!Array.isArray(value)) {
    throw new ValidationError(
      `${fieldName} must be an array`,
      fieldName,
      value
    );
  }
}

/**
 * Validate that a value is one of the allowed values
 * @param {*} value - Value to validate
 * @param {string} fieldName - Name of the field
 * @param {Array} allowedValues - Array of allowed values
 * @throws {ValidationError} If value is not in allowedValues
 */
function validateEnum(value, fieldName, allowedValues) {
  if (!allowedValues.includes(value)) {
    throw new ValidationError(
      `${fieldName} must be one of: ${allowedValues.join(', ')}`,
      fieldName,
      value
    );
  }
}

/**
 * Validate customer ID format
 * @param {string} customerId - Customer ID to validate
 * @throws {ValidationError} If customer ID is invalid
 */
function validateCustomerId(customerId) {
  validateRequired({ customerId }, ['customerId']);
  validateString(customerId, 'customerId');

  if (customerId.length < 1) {
    throw new ValidationError(
      'customerId cannot be empty',
      'customerId',
      customerId
    );
  }
}

/**
 * Validate site ID format
 * @param {string} siteId - Site ID to validate
 * @throws {ValidationError} If site ID is invalid
 */
function validateSiteId(siteId) {
  validateRequired({ siteId }, ['siteId']);
  validateString(siteId, 'siteId');

  if (siteId.length < 1) {
    throw new ValidationError(
      'siteId cannot be empty',
      'siteId',
      siteId
    );
  }
}

/**
 * Validate device ID format
 * @param {string} deviceId - Device ID to validate
 * @throws {ValidationError} If device ID is invalid
 */
function validateDeviceId(deviceId) {
  validateRequired({ deviceId }, ['deviceId']);
  validateString(deviceId, 'deviceId');

  if (deviceId.length < 1) {
    throw new ValidationError(
      'deviceId cannot be empty',
      'deviceId',
      deviceId
    );
  }
}

/**
 * Validate asset ID format
 * @param {string} assetId - Asset ID to validate
 * @throws {ValidationError} If asset ID is invalid
 */
function validateAssetId(assetId) {
  validateRequired({ assetId }, ['assetId']);
  validateString(assetId, 'assetId');

  if (assetId.length < 1) {
    throw new ValidationError(
      'assetId cannot be empty',
      'assetId',
      assetId
    );
  }
}

module.exports = {
  validateRequired,
  validateString,
  validateNumber,
  validatePositiveNumber,
  validateRange,
  validateArray,
  validateEnum,
  validateCustomerId,
  validateSiteId,
  validateDeviceId,
  validateAssetId
};
