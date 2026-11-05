"""Service clients for Ona Platform SDK."""

from __future__ import annotations

from .anomaly import AnomalyClient
from .asset_intelligence import AssetIntelligenceClient
from .auth import AuthClient
from .data_ingestion import DataIngestionClient
from .edge_device import EdgeDeviceClient
from .energy_analyst import EnergyAnalystClient
from .enphase import EnphaseClient
from .forecasting import ForecastingClient
from .huawei import HuaweiClient
from .interpolation import InterpolationClient
from .list_huawei import ListHuaweiCustomersClient
from .partner_api import PartnerApiClient
from .solar_resource import SolarResourceClient
from .standardization import StandardizationClient
from .terminal import TerminalClient
from .training import TrainingClient
from .weather import WeatherClient

__all__ = [
    "AnomalyClient",
    "AssetIntelligenceClient",
    "AuthClient",
    "DataIngestionClient",
    "EdgeDeviceClient",
    "EnergyAnalystClient",
    "EnphaseClient",
    "ForecastingClient",
    "HuaweiClient",
    "InterpolationClient",
    "ListHuaweiCustomersClient",
    "PartnerApiClient",
    "SolarResourceClient",
    "StandardizationClient",
    "TerminalClient",
    "TrainingClient",
    "WeatherClient",
]
