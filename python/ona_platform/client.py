"""Main client for Ona Platform SDK."""

import logging
from typing import Optional

from .config import OnaConfig
from .services import (
    ForecastingClient,
    TerminalClient,
    EnergyAnalystClient,
    EdgeDeviceClient,
    WeatherClient,
    EnphaseClient,
    HuaweiClient,
    DataIngestionClient,
    InterpolationClient,
    StandardizationClient,
    TrainingClient,
    InverterTelemetryClient,
    OodaTerminalClient,
)

logger = logging.getLogger(__name__)


class OnaClient:
    """Main client for Ona Energy Management Platform.

    Provides unified access to all platform services through a single interface.

    Example:
        >>> from ona_platform import OnaClient
        >>> client = OnaClient()  # Uses environment variables
        >>>
        >>> # Or with explicit configuration
        >>> client = OnaClient(
        ...     aws_region='af-south-1',
        ...     energy_analyst_url='http://localhost:8000'
        ... )
        >>>
        >>> # Use service clients
        >>> forecast = client.forecasting.get_site_forecast('Sibaya')
        >>> answer = client.energy_analyst.query("What are NRS requirements?")
    """

    def __init__(
        self,
        config: Optional[OnaConfig] = None,
        aws_region: Optional[str] = None,
        input_bucket: Optional[str] = None,
        output_bucket: Optional[str] = None,
        lambda_endpoint_url: Optional[str] = None,
        edge_api_url: Optional[str] = None,
        energy_analyst_url: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        inverter_telemetry_endpoint: Optional[str] = None,
        inverter_telemetry_api_key: Optional[str] = None,
        ooda_terminal_endpoint: Optional[str] = None,
        ooda_terminal_api_key: Optional[str] = None,
    ):
        """Initialize Ona Platform client.

        Args:
            config: Pre-configured OnaConfig instance
            aws_region: AWS region (default: af-south-1)
            input_bucket: S3 input bucket
            output_bucket: S3 output bucket
            lambda_endpoint_url: Base URL for Lambda endpoints
            edge_api_url: Edge device service URL
            energy_analyst_url: Energy Analyst RAG service URL
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        If config is not provided, configuration will be created from
        environment variables and/or provided parameters.
        """
        if config is None:
            # Load from environment first
            config = OnaConfig.from_env()

            # Override with provided parameters
            if aws_region is not None:
                config.aws_region = aws_region
            if input_bucket is not None:
                config.input_bucket = input_bucket
            if output_bucket is not None:
                config.output_bucket = output_bucket
            if lambda_endpoint_url is not None:
                config.lambda_endpoint_url = lambda_endpoint_url
            if edge_api_url is not None:
                config.edge_api_url = edge_api_url
            if energy_analyst_url is not None:
                config.energy_analyst_url = energy_analyst_url
            if timeout is not None:
                config.timeout = timeout
            if max_retries is not None:
                config.max_retries = max_retries
            if inverter_telemetry_endpoint is not None:
                config.inverter_telemetry_endpoint = inverter_telemetry_endpoint
            if inverter_telemetry_api_key is not None:
                config.inverter_telemetry_api_key = inverter_telemetry_api_key
            if ooda_terminal_endpoint is not None:
                config.ooda_terminal_endpoint = ooda_terminal_endpoint
            if ooda_terminal_api_key is not None:
                config.ooda_terminal_api_key = ooda_terminal_api_key

        self.config = config

        # Initialize service clients (lazy-loaded)
        self._forecasting = None
        self._terminal = None
        self._energy_analyst = None
        self._edge_devices = None
        self._weather = None
        self._enphase = None
        self._huawei = None
        self._data_ingestion = None
        self._interpolation = None
        self._standardization = None
        self._training = None
        self._inverter_telemetry = None
        self._ooda_terminal = None

        logger.info("Ona Platform client initialized")
        logger.debug(f"Configuration: {self.config}")

    @property
    def forecasting(self) -> ForecastingClient:
        """Get Forecasting service client."""
        if self._forecasting is None:
            self._forecasting = ForecastingClient(self.config)
        return self._forecasting

    @property
    def terminal(self) -> TerminalClient:
        """Get Terminal API client (OODA workflow)."""
        if self._terminal is None:
            self._terminal = TerminalClient(self.config)
        return self._terminal

    @property
    def energy_analyst(self) -> EnergyAnalystClient:
        """Get Energy Analyst RAG service client."""
        if self._energy_analyst is None:
            self._energy_analyst = EnergyAnalystClient(self.config)
        return self._energy_analyst

    @property
    def edge_devices(self) -> EdgeDeviceClient:
        """Get Edge Device Registry client."""
        if self._edge_devices is None:
            self._edge_devices = EdgeDeviceClient(self.config)
        return self._edge_devices

    @property
    def weather(self) -> WeatherClient:
        """Get Weather Cache service client."""
        if self._weather is None:
            self._weather = WeatherClient(self.config)
        return self._weather

    @property
    def enphase(self) -> EnphaseClient:
        """Get Enphase data collection client."""
        if self._enphase is None:
            self._enphase = EnphaseClient(self.config)
        return self._enphase

    @property
    def huawei(self) -> HuaweiClient:
        """Get Huawei data collection client."""
        if self._huawei is None:
            self._huawei = HuaweiClient(self.config)
        return self._huawei

    @property
    def data_ingestion(self) -> DataIngestionClient:
        """Get Data Ingestion service client."""
        if self._data_ingestion is None:
            self._data_ingestion = DataIngestionClient(self.config)
        return self._data_ingestion

    @property
    def interpolation(self) -> InterpolationClient:
        """Get Interpolation service client."""
        if self._interpolation is None:
            self._interpolation = InterpolationClient(self.config)
        return self._interpolation

    @property
    def standardization(self) -> StandardizationClient:
        """Get Data Standardization service client."""
        if self._standardization is None:
            self._standardization = StandardizationClient(self.config)
        return self._standardization

    @property
    def training(self) -> TrainingClient:
        """Get Global Training service client."""
        if self._training is None:
            self._training = TrainingClient(self.config)
        return self._training

    @property
    def inverter_telemetry(self) -> InverterTelemetryClient:
        """Get Inverter Telemetry service client."""
        if self._inverter_telemetry is None:
            self._inverter_telemetry = InverterTelemetryClient(self.config)
        return self._inverter_telemetry

    @property
    def ooda_terminal(self) -> OodaTerminalClient:
        """Get OODA Terminal API service client."""
        if self._ooda_terminal is None:
            self._ooda_terminal = OodaTerminalClient(self.config)
        return self._ooda_terminal
