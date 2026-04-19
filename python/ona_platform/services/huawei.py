"""Huawei data collection service clients."""

import logging
from typing import Any, Dict

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class HuaweiClient(BaseServiceClient):
    """Client for Huawei data collection services.

    Provides methods for both real-time and historical data collection.
    """

    def __init__(
        self,
        config: OnaConfig,
        realtime_function: str = "huaweiRealTime",
        historical_function: str = "huaweiHistorical",
    ):
        """Initialize Huawei client.

        Args:
            config: SDK configuration
            realtime_function: Lambda function name for real-time data
            historical_function: Lambda function name for historical data
        """
        super().__init__(config)
        self.realtime_function = realtime_function
        self.historical_function = historical_function

    def collect_realtime(self, plant_code: str, **kwargs) -> Dict[str, Any]:
        """Collect real-time data from Huawei system.

        Args:
            plant_code: Huawei plant code
            **kwargs: Additional parameters for data collection

        Returns:
            Collection status and data summary
        """
        payload = {"plant_code": plant_code, **kwargs}
        logger.info(f"Collecting real-time Huawei data for plant: {plant_code}")
        return self.invoke_lambda(self.realtime_function, payload)

    def collect_historical(
        self, plant_code: str, start_date: str, end_date: str, **kwargs
    ) -> Dict[str, Any]:
        """Collect historical data from Huawei system.

        Args:
            plant_code: Huawei plant code
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            **kwargs: Additional parameters for data collection

        Returns:
            Collection status and data summary
        """
        payload = {
            "plant_code": plant_code,
            "start_date": start_date,
            "end_date": end_date,
            **kwargs,
        }
        logger.info(
            f"Collecting historical Huawei data for plant: {plant_code} "
            f"({start_date} to {end_date})"
        )
        return self.invoke_lambda(self.historical_function, payload)
