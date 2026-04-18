/**
 * Custom error classes for Ona SDK
 */

/**
 * Base error class for all SDK errors
 */
class OnaSDKError extends Error {
  constructor(message, code = 'SDK_ERROR', details = {}) {
    super(message);
    this.name = 'OnaSDKError';
    this.code = code;
    this.details = details;
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * Error thrown when API request fails
 */
class APIError extends OnaSDKError {
  constructor(message, statusCode, response = null) {
    super(message, 'API_ERROR', { statusCode, response });
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.response = response;
  }
}

/**
 * Error thrown when configuration is invalid
 */
class ConfigurationError extends OnaSDKError {
  constructor(message, missingFields = []) {
    super(message, 'CONFIGURATION_ERROR', { missingFields });
    this.name = 'ConfigurationError';
    this.missingFields = missingFields;
  }
}

/**
 * Error thrown when input validation fails
 */
class ValidationError extends OnaSDKError {
  constructor(message, field, value) {
    super(message, 'VALIDATION_ERROR', { field, value });
    this.name = 'ValidationError';
    this.field = field;
    this.value = value;
  }
}

/**
 * Error thrown when authentication fails
 */
class AuthenticationError extends OnaSDKError {
  constructor(message) {
    super(message, 'AUTHENTICATION_ERROR');
    this.name = 'AuthenticationError';
  }
}

/**
 * Error thrown when network request times out
 */
class TimeoutError extends OnaSDKError {
  constructor(message, timeout) {
    super(message, 'TIMEOUT_ERROR', { timeout });
    this.name = 'TimeoutError';
    this.timeout = timeout;
  }
}

/**
 * Error thrown when backend rate limit is exceeded (HTTP 429)
 */
class RateLimitError extends OnaSDKError {
  constructor(message) {
    super(message, 'RATE_LIMIT_ERROR');
    this.name = 'RateLimitError';
  }
}

/**
 * Error thrown when service is unavailable after retries exhausted
 */
class ServiceUnavailableError extends OnaSDKError {
  constructor(message) {
    super(message, 'SERVICE_UNAVAILABLE_ERROR');
    this.name = 'ServiceUnavailableError';
  }
}

module.exports = {
  OnaSDKError,
  APIError,
  ConfigurationError,
  ValidationError,
  AuthenticationError,
  TimeoutError,
  RateLimitError,
  ServiceUnavailableError
};
