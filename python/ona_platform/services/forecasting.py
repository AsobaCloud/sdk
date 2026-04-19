"""Forecasting API client."""

import logging
from typing import Dict, Any

from .base import BaseServiceClient
from ..config import OnaConfig

logger = logging.getLogger(__name__)


class ForecastingClient(BaseServiceClient):
    """Client for solar energy forecasting service.

    Provides methods for device-level, site-level, and customer-level forecasting.
    """

    def __init__(self, config: OnaConfig, function_name: str = "forecastingApi"):
        """Initialize forecasting client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for forecasting service
        """
        super().__init__(config)
        self.function_name = function_name

    def get_device_forecast(
        self, site_id: str, device_id: str, forecast_hours: int = 24
    ) -> Dict[str, Any]:
        """Get forecast for a specific device.

        Args:
            site_id: Site identifier
            device_id: Device identifier
            forecast_hours: Number of hours to forecast (default: 24)

        Returns:
            Device forecast data with predictions

        Example:
            >>> client.forecasting.get_device_forecast('Sibaya', 'INV001', 24)
            {
                'site_id': 'Sibaya',
                'device_id': 'INV001',
                'forecasts': [...],
                'model_info': {...}
            }
        """
        payload = {"site_id": site_id, "device_id": device_id, "forecast_hours": forecast_hours}

        logger.info(
            f"Getting device forecast: site={site_id}, device={device_id}, hours={forecast_hours}"
        )

        return self.invoke_lambda(self.function_name, payload)

    def get_site_forecast(
        self, site_id: str, forecast_hours: int = 24, include_device_breakdown: bool = False
    ) -> Dict[str, Any]:
        """Get aggregated forecast for an entire site.

        Args:
            site_id: Site identifier
            forecast_hours: Number of hours to forecast (default: 24)
            include_device_breakdown: Include individual device forecasts

        Returns:
            Site forecast data aggregated from all devices

        Example:
            >>> client.forecasting.get_site_forecast('Sibaya', 24, True)
            {
                'site_id': 'Sibaya',
                'forecasts': [...],
                'devices_included': ['INV001', 'INV002'],
                'device_forecasts': [...]  # if include_device_breakdown=True
            }
        """
        payload = {
            "site_id": site_id,
            "forecast_hours": forecast_hours,
            "include_device_breakdown": include_device_breakdown,
        }

        logger.info(
            f"Getting site forecast: site={site_id}, hours={forecast_hours}, "
            f"breakdown={include_device_breakdown}"
        )

        return self.invoke_lambda(self.function_name, payload)

    def get_customer_forecast(self, customer_id: str, forecast_hours: int = 24) -> Dict[str, Any]:
        """Get forecast for a customer (legacy method).

        Args:
            customer_id: Customer identifier
            forecast_hours: Number of hours to forecast (default: 24)

        Returns:
            Customer forecast data

        Example:
            >>> client.forecasting.get_customer_forecast('customer123', 24)
            {
                'customer_id': 'customer123',
                'forecasts': [...],
                'model_info': {...}
            }
        """
        payload = {"customer_id": customer_id, "forecast_hours": forecast_hours}

        logger.info(f"Getting customer forecast: customer={customer_id}, hours={forecast_hours}")

        return self.invoke_lambda(self.function_name, payload)
