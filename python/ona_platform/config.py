"""Configuration management for Ona Platform SDK."""

import os
from typing import Optional
from dataclasses import dataclass
from .exceptions import ConfigurationError


@dataclass
class OnaConfig:
    """Configuration for Ona Platform SDK.

    Attributes:
        aws_region: AWS region for services (default: af-south-1)
        input_bucket: S3 bucket for input data
        output_bucket: S3 bucket for output data
        lambda_endpoint_url: Base URL for Lambda endpoints
        edge_api_url: Base URL for edge device services
        energy_analyst_url: URL for EnergyAnalyst RAG service
        timeout: Default timeout for requests in seconds
        max_retries: Maximum number of retry attempts
        retry_backoff: Backoff multiplier for retries
    """

    aws_region: str = "af-south-1"
    input_bucket: str = "sa-api-client-input"
    output_bucket: str = "sa-api-client-output"
    lambda_endpoint_url: Optional[str] = None
    edge_api_url: Optional[str] = None
    energy_analyst_url: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    retry_backoff: float = 2.0
    inverter_telemetry_endpoint: Optional[str] = None
    inverter_telemetry_api_key: Optional[str] = None
    telemetry_polling_interval: float = 5.0
    telemetry_5min_table: str = "ona-platform-telemetry-5min"
    telemetry_daily_table: str = "ona-platform-telemetry-daily"
    ooda_terminal_endpoint: Optional[str] = None
    ooda_terminal_api_key: Optional[str] = None
    ooda_polling_interval: float = 5.0
    ooda_5min_table: str = "ona-platform-ooda-5min"
    ooda_daily_table: str = "ona-platform-ooda-daily"

    def __post_init__(self):
        if self.inverter_telemetry_endpoint is not None:
            if not self.inverter_telemetry_endpoint.startswith("https://"):
                raise ConfigurationError(
                    f"inverter_telemetry_endpoint must use https:// (got: {self.inverter_telemetry_endpoint!r})"
                )
        if self.ooda_terminal_endpoint is not None:
            if not self.ooda_terminal_endpoint.startswith("https://"):
                raise ConfigurationError(
                    f"ooda_terminal_endpoint must use https:// (got: {self.ooda_terminal_endpoint!r})"
                )
        if self.telemetry_polling_interval < 1.0:
            raise ConfigurationError(
                f"telemetry_polling_interval must be >= 1.0 seconds (got: {self.telemetry_polling_interval})"
            )
        if self.ooda_polling_interval < 1.0:
            raise ConfigurationError(
                f"ooda_polling_interval must be >= 1.0 seconds (got: {self.ooda_polling_interval})"
            )

    @classmethod
    def from_env(cls) -> "OnaConfig":
        """Create configuration from environment variables.

        Environment variables:
            AWS_REGION: AWS region
            INPUT_BUCKET: S3 input bucket
            OUTPUT_BUCKET: S3 output bucket
            LAMBDA_ENDPOINT_URL: Lambda endpoint URL
            EDGE_API_URL: Edge device API URL
            ENERGY_ANALYST_URL: Energy Analyst RAG service URL
            ONA_TIMEOUT: Request timeout in seconds
            ONA_MAX_RETRIES: Maximum retry attempts

        Returns:
            OnaConfig instance with values from environment
        """
        return cls(
            aws_region=os.getenv("AWS_REGION", "af-south-1"),
            input_bucket=os.getenv("INPUT_BUCKET", "sa-api-client-input"),
            output_bucket=os.getenv("OUTPUT_BUCKET", "sa-api-client-output"),
            lambda_endpoint_url=os.getenv("LAMBDA_ENDPOINT_URL"),
            edge_api_url=os.getenv("EDGE_API_URL"),
            energy_analyst_url=os.getenv("ENERGY_ANALYST_URL"),
            timeout=int(os.getenv("ONA_TIMEOUT", "120")),
            max_retries=int(os.getenv("ONA_MAX_RETRIES", "3")),
            retry_backoff=float(os.getenv("ONA_RETRY_BACKOFF", "2.0")),
            inverter_telemetry_endpoint=os.getenv("INVERTER_TELEMETRY_ENDPOINT"),
            inverter_telemetry_api_key=os.getenv("INVERTER_TELEMETRY_API_KEY"),
            telemetry_polling_interval=float(os.getenv("TELEMETRY_POLLING_INTERVAL", "5.0")),
            telemetry_5min_table=os.getenv("TELEMETRY_5MIN_TABLE", "ona-platform-telemetry-5min"),
            telemetry_daily_table=os.getenv("TELEMETRY_DAILY_TABLE", "ona-platform-telemetry-daily"),
            ooda_terminal_endpoint=os.getenv("OODA_TERMINAL_ENDPOINT"),
            ooda_terminal_api_key=os.getenv("OODA_TERMINAL_API_KEY"),
            ooda_polling_interval=float(os.getenv("OODA_POLLING_INTERVAL", "5.0")),
            ooda_5min_table=os.getenv("OODA_5MIN_TABLE", "ona-platform-ooda-5min"),
            ooda_daily_table=os.getenv("OODA_DAILY_TABLE", "ona-platform-ooda-daily"),
        )
