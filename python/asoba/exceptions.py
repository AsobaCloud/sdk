"""Custom exceptions for Ona Platform SDK."""

from __future__ import annotations


class OnaError(Exception):
    """Base exception for all Ona Platform SDK errors."""


class ConfigurationError(OnaError):
    """Raised when SDK configuration is invalid."""


class ServiceUnavailableError(OnaError):
    """Raised when a service is unavailable or returns 5xx error."""


class ValidationError(OnaError):
    """Raised when request validation fails."""


class AuthenticationError(OnaError):
    """Raised when authentication fails."""


class ResourceNotFoundError(OnaError):
    """Raised when a requested resource is not found (404)."""


class RateLimitError(OnaError):
    """Raised when rate limit is exceeded."""


class TimeoutError(OnaError):
    """Raised when a request times out."""
