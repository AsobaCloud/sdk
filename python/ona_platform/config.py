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
        auth_endpoint: URL for authentication service
        partner_api_endpoint: URL for Partner API (snapshots)
        partner_api_key: API key for Partner API
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
    auth_endpoint: Optional[str] = None
    partner_api_endpoint: Optional[str] = None
    partner_api_key: Optional[str] = None
    timeout: int = 120
    max_retries: int = 3
    retry_backoff: float = 2.0

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.partner_api_endpoint and not self.partner_api_endpoint.startswith("https://"):
            raise ConfigurationError("partner_api_endpoint must use https://")

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
            PARTNER_API_ENDPOINT: Partner API endpoint URL
            PARTNER_API_KEY: Partner API key
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
            auth_endpoint=os.getenv("ONA_AUTH_ENDPOINT"),
            partner_api_endpoint=os.getenv("PARTNER_API_ENDPOINT"),
            partner_api_key=os.getenv("PARTNER_API_KEY"),
            timeout=int(os.getenv("ONA_TIMEOUT", "120")),
            max_retries=int(os.getenv("ONA_MAX_RETRIES", "3")),
            retry_backoff=float(os.getenv("ONA_RETRY_BACKOFF", "2.0"))
        )
