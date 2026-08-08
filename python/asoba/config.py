"""Configuration management for Ona Platform SDK."""

from __future__ import annotations

import os
from dataclasses import dataclass

from .exceptions import ConfigurationError


@dataclass
class OnaConfig:
    """Configuration for the Ona SDK.

    The only required field is api_key (or ASOBA_API_KEY env var).
    All endpoint URLs default to the canonical production values.

    Attributes:
        api_key: API key for the telemetry, OODA, and partner APIs.
            Set via ASOBA_API_KEY environment variable or constructor.
        telemetry_endpoint: Inverter Telemetry API base URL.
        ooda_endpoint: OODA Terminal API base URL.
        partner_endpoint: Partner API base URL.
        terminal_endpoint: Terminal/OODA workflow API base URL (JWT auth).
        auth_endpoint: User-management auth Lambda URL (for login/JWT).
        timeout: Request timeout in seconds (default 120).
        max_retries: Maximum retry attempts (default 3).
        retry_backoff: Backoff multiplier for retries (default 2.0).
        telemetry_polling_interval: Polling interval for streaming (default 5.0s).
        ooda_polling_interval: Polling interval for OODA streaming (default 5.0s).

    Internal / advanced:
        aws_region: AWS region (used by internal Lambda-based clients).
        input_bucket: S3 input bucket (internal).
        output_bucket: S3 output bucket (internal).
        edge_api_url: Edge device registry URL (internal).
        energy_analyst_url: Energy Analyst RAG URL (internal).
    """

    # --- Primary credential ---
    api_key: str | None = None

    # --- Canonical endpoint defaults ---
    telemetry_endpoint: str = "https://telemetry.api.asoba.co"
    ooda_endpoint: str = "https://ooda.api.asoba.co"
    partner_endpoint: str = "https://partner.api.asoba.co"
    terminal_endpoint: str = "https://api.asoba.co"
    auth_endpoint: str | None = None

    # --- Request tuning ---
    timeout: int = 120
    max_retries: int = 3
    retry_backoff: float = 2.0
    telemetry_polling_interval: float = 5.0
    ooda_polling_interval: float = 5.0

    # --- Internal / advanced ---
    aws_region: str = "af-south-1"
    input_bucket: str = "sa-api-client-input"
    output_bucket: str = "sa-api-client-output"
    edge_api_url: str | None = None
    energy_analyst_url: str | None = None

    def __post_init__(self):
        if self.partner_endpoint and not self.partner_endpoint.startswith("https://"):
            raise ConfigurationError("partner_endpoint must use https://")

    @classmethod
    def from_env(cls) -> OnaConfig:
        """Create configuration from environment variables.

        Primary:
            ASOBA_API_KEY: API key for telemetry, OODA, and partner APIs.

        Optional overrides:
            ASOBA_TELEMETRY_ENDPOINT, ASOBA_OODA_ENDPOINT,
            ASOBA_PARTNER_ENDPOINT, ASOBA_TERMINAL_ENDPOINT,
            ASOBA_AUTH_ENDPOINT, ONA_TIMEOUT, ONA_MAX_RETRIES
        """
        return cls(
            api_key=os.getenv("ASOBA_API_KEY"),
            telemetry_endpoint=os.getenv(
                "ASOBA_TELEMETRY_ENDPOINT", "https://telemetry.api.asoba.co"
            ),
            ooda_endpoint=os.getenv(
                "ASOBA_OODA_ENDPOINT", "https://ooda.api.asoba.co"
            ),
            partner_endpoint=os.getenv(
                "ASOBA_PARTNER_ENDPOINT", "https://partner.api.asoba.co"
            ),
            terminal_endpoint=os.getenv(
                "ASOBA_TERMINAL_ENDPOINT", "https://api.asoba.co"
            ),
            auth_endpoint=os.getenv("ASOBA_AUTH_ENDPOINT"),
            timeout=int(os.getenv("ONA_TIMEOUT", "120")),
            max_retries=int(os.getenv("ONA_MAX_RETRIES", "3")),
            retry_backoff=float(os.getenv("ONA_RETRY_BACKOFF", "2.0")),
            aws_region=os.getenv("AWS_REGION", "af-south-1"),
            input_bucket=os.getenv("INPUT_BUCKET", "sa-api-client-input"),
            output_bucket=os.getenv("OUTPUT_BUCKET", "sa-api-client-output"),
            edge_api_url=os.getenv("EDGE_API_URL"),
            energy_analyst_url=os.getenv("ENERGY_ANALYST_URL"),
        )
