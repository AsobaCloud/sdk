"""Main client for Ona Platform SDK."""

from __future__ import annotations

import logging

from .config import OnaConfig
from .services import (
    AuthClient,
    DataIngestionClient,
    EdgeDeviceClient,
    EnergyAnalystClient,
    EnphaseClient,
    ForecastingClient,
    HuaweiClient,
    InterpolationClient,
    PartnerApiClient,
    StandardizationClient,
    TerminalClient,
    TrainingClient,
    WeatherClient,
)

logger = logging.getLogger(__name__)


class OnaClient:
    """Main client for the Ona Energy Management Platform.

    Usage::

        from asoba import OnaClient

        # From environment variable ASOBA_API_KEY
        client = OnaClient()

        # Explicit key
        client = OnaClient(api_key="your_key")

        # Query inverter telemetry
        records = client.inverter_telemetry.get_inverter_telemetry(
            asset_id="INV-1000000054495190",
            site_id="Sibaya",
            time_range={"start": "2025-11-01T00:00:00", "end": "2025-11-01T12:00:00"},
        )

        # Terminal API — login once, JWT managed automatically
        client.auth.login("user@example.com", "password")
        assets = client.terminal.list_assets(customer_id="Sibaya")
    """

    def __init__(
        self,
        config: OnaConfig | None = None,
        api_key: str | None = None,
        auth_endpoint: str | None = None,
        terminal_endpoint: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
        # Advanced / internal overrides
        aws_region: str | None = None,
        edge_api_url: str | None = None,
        energy_analyst_url: str | None = None,
    ):
        """Initialize the Ona SDK client.

        Args:
            api_key: API key for telemetry, OODA, and partner APIs.
                     Falls back to ASOBA_API_KEY environment variable.
            auth_endpoint: Override the auth service URL.
            terminal_endpoint: Override the terminal API URL
                               (default: https://api.asoba.co).
            timeout: Request timeout in seconds (default 120).
            max_retries: Maximum retry attempts (default 3).
            config: Supply a fully-constructed OnaConfig instead of
                    individual parameters.
        """
        if config is None:
            config = OnaConfig.from_env()
            if api_key is not None:
                config.api_key = api_key
            if auth_endpoint is not None:
                config.auth_endpoint = auth_endpoint
            if terminal_endpoint is not None:
                config.terminal_endpoint = terminal_endpoint
            if timeout is not None:
                config.timeout = timeout
            if max_retries is not None:
                config.max_retries = max_retries
            if aws_region is not None:
                config.aws_region = aws_region
            if edge_api_url is not None:
                config.edge_api_url = edge_api_url
            if energy_analyst_url is not None:
                config.energy_analyst_url = energy_analyst_url

        self.config = config

        # Lazy-loaded service clients
        self._auth = None
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
        self._partner = None
        self._inverter_telemetry = None
        self._ooda_terminal = None

        logger.debug("OnaClient initialized")

    # ------------------------------------------------------------------
    # Service accessors
    # ------------------------------------------------------------------

    @property
    def auth(self) -> AuthClient:
        """Authentication client — login, token management."""
        if self._auth is None:
            self._auth = AuthClient(self.config)
        return self._auth

    @property
    def inverter_telemetry(self):
        """Inverter Telemetry API client."""
        if self._inverter_telemetry is None:
            from .services.inverter_telemetry import InverterTelemetryClient
            self._inverter_telemetry = InverterTelemetryClient(self.config)
        return self._inverter_telemetry

    @property
    def ooda_terminal(self):
        """OODA Terminal Alerts API client."""
        if self._ooda_terminal is None:
            from .services.ooda_terminal import OodaTerminalClient
            self._ooda_terminal = OodaTerminalClient(self.config)
        return self._ooda_terminal

    @property
    def partner(self) -> PartnerApiClient:
        """Partner API client — KPI snapshots, maintenance signals, forecasts."""
        if self._partner is None:
            self._partner = PartnerApiClient(self.config)
        return self._partner

    @property
    def terminal(self) -> TerminalClient:
        """Terminal API client — OODA workflow (requires login via auth)."""
        if self._terminal is None:
            self._terminal = TerminalClient(self.config, auth_client=self.auth)
        return self._terminal

    @property
    def forecasting(self) -> ForecastingClient:
        """Forecasting service client (internal)."""
        if self._forecasting is None:
            self._forecasting = ForecastingClient(self.config)
        return self._forecasting

    @property
    def energy_analyst(self) -> EnergyAnalystClient:
        """Energy Analyst RAG client (internal)."""
        if self._energy_analyst is None:
            self._energy_analyst = EnergyAnalystClient(self.config)
        return self._energy_analyst

    @property
    def edge_devices(self) -> EdgeDeviceClient:
        """Edge Device Registry client (internal)."""
        if self._edge_devices is None:
            self._edge_devices = EdgeDeviceClient(self.config)
        return self._edge_devices

    @property
    def weather(self) -> WeatherClient:
        """Weather Cache client (internal)."""
        if self._weather is None:
            self._weather = WeatherClient(self.config)
        return self._weather

    @property
    def enphase(self) -> EnphaseClient:
        """Enphase data collection client (internal)."""
        if self._enphase is None:
            self._enphase = EnphaseClient(self.config)
        return self._enphase

    @property
    def huawei(self) -> HuaweiClient:
        """Huawei data collection client (internal)."""
        if self._huawei is None:
            self._huawei = HuaweiClient(self.config)
        return self._huawei

    @property
    def data_ingestion(self) -> DataIngestionClient:
        """Data ingestion client (internal)."""
        if self._data_ingestion is None:
            self._data_ingestion = DataIngestionClient(self.config)
        return self._data_ingestion

    @property
    def interpolation(self) -> InterpolationClient:
        """Interpolation client (internal)."""
        if self._interpolation is None:
            self._interpolation = InterpolationClient(self.config)
        return self._interpolation

    @property
    def standardization(self) -> StandardizationClient:
        """Data standardization client (internal)."""
        if self._standardization is None:
            self._standardization = StandardizationClient(self.config)
        return self._standardization

    @property
    def training(self) -> TrainingClient:
        """ML training client (internal)."""
        if self._training is None:
            self._training = TrainingClient(self.config)
        return self._training

    # gap_detection convenience alias
    @property
    def gap_detection(self):
        """Gap detection client (internal)."""
        from .services.gap_detection import GapDetectionClient
        return GapDetectionClient(self.config)
