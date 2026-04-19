"""Ona Platform SDK - Python client for Ona Energy Management Platform.

This SDK provides a unified interface to all Ona Platform services including:
- Solar energy forecasting
- OODA workflow (asset management, fault detection, diagnostics, scheduling)
- Energy policy analysis with RAG
- Edge device management
- Data collection and processing
- ML model training

Quick Start:
    >>> from ona_platform import OnaClient
    >>>
    >>> # Initialize client (uses environment variables)
    >>> client = OnaClient()
    >>>
    >>> # Get solar forecast
    >>> forecast = client.forecasting.get_site_forecast('Sibaya', hours=24)
    >>>
    >>> # Query energy policies
    >>> answer = client.energy_analyst.query(
    ...     "What are the grid code requirements for solar installations?"
    ... )
    >>>
    >>> # Run fault detection
    >>> detection = client.terminal.run_detection(
    ...     customer_id='customer123',
    ...     asset_id='asset456'
    ... )
"""

from .client import OnaClient
from .config import OnaConfig
from .exceptions import (
    OnaError,
    ConfigurationError,
    ServiceUnavailableError,
    ValidationError,
    AuthenticationError,
    ResourceNotFoundError,
    RateLimitError,
    TimeoutError,
)
from .services.inverter_telemetry import InverterTelemetryClient
from .models.telemetry import TelemetryRecord, TimeRange, CursorObject

__version__ = "1.0.0"

__all__ = [
    "OnaClient",
    "OnaConfig",
    "OnaError",
    "ConfigurationError",
    "ServiceUnavailableError",
    "ValidationError",
    "AuthenticationError",
    "ResourceNotFoundError",
    "RateLimitError",
    "TimeoutError",
    "InverterTelemetryClient",
    "TelemetryRecord",
    "TimeRange",
    "CursorObject",
]
