"""Enphase data collection service clients."""

import logging
from typing import Dict, Any

from .base import BaseServiceClient
from ..config import OnaConfig

logger = logging.getLogger(__name__)


class EnphaseClient(BaseServiceClient):
    """Client for Enphase data collection services.

    Provides methods for both real-time and historical data collection.
    """

    def __init__(
        self,
        config: OnaConfig,
        realtime_function: str = "enphaseRealTime",
        historical_function: str = "enphaseHistorical"
    ):
        """Initialize Enphase client.

        Args:
            config: SDK configuration
            realtime_function: Lambda function name for real-time data
            historical_function: Lambda function name for historical data
        """
        super().__init__(config)
        self.realtime_function = realtime_function
        self.historical_function = historical_function

    def collect_realtime(self, site_id: str, **kwargs) -> Dict[str, Any]:
        """Collect real-time data from Enphase system.

        Args:
            site_id: Enphase site identifier
            **kwargs: Additional parameters for data collection

        Returns:
            Collection status and data summary
        """
        payload = {"site_id": site_id, **kwargs}
        logger.info(f"Collecting real-time Enphase data for site: {site_id}")
        return self.invoke_lambda(self.realtime_function, payload)

    def collect_historical(
        self,
        site_id: str,
        start_date: str,
        end_date: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Collect historical data from Enphase system.

        Args:
            site_id: Enphase site identifier
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            **kwargs: Additional parameters for data collection

        Returns:
            Collection status and data summary
        """
        payload = {
            "site_id": site_id,
            "start_date": start_date,
            "end_date": end_date,
            **kwargs
        }
        logger.info(
            f"Collecting historical Enphase data for site: {site_id} "
            f"({start_date} to {end_date})"
        )
        return self.invoke_lambda(self.historical_function, payload)
