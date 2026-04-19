"""Custom exceptions for Ona Platform SDK."""


class OnaError(Exception):
    """Base exception for all Ona Platform SDK errors."""

    pass


class ConfigurationError(OnaError):
    """Raised when SDK configuration is invalid."""

    pass


class ServiceUnavailableError(OnaError):
    """Raised when a service is unavailable or returns 5xx error."""

    pass


class ValidationError(OnaError):
    """Raised when request validation fails."""

    pass


class AuthenticationError(OnaError):
    """Raised when authentication fails."""

    pass


class ResourceNotFoundError(OnaError):
    """Raised when a requested resource is not found (404)."""

    pass


class RateLimitError(OnaError):
    """Raised when rate limit is exceeded."""

    pass


class TimeoutError(OnaError):
    """Raised when a request times out."""

    pass
