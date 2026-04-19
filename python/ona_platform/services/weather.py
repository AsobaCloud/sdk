"""Weather Cache service client."""

import logging
from typing import Any, Dict

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class WeatherClient(BaseServiceClient):
    """Client for Weather Cache service.

    Provides methods for accessing cached weather data.
    """

    def __init__(self, config: OnaConfig, function_name: str = "weatherCache"):
        """Initialize weather client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for weather service
        """
        super().__init__(config)
        self.function_name = function_name

    def trigger_update(self) -> Dict[str, Any]:
        """Trigger weather cache update for all locations.

        Returns:
            Update status and number of locations updated
        """
        payload = {"action": "update"}
        logger.info("Triggering weather cache update")
        return self.invoke_lambda(self.function_name, payload)

    def get_cached_weather(self, location: str) -> Dict[str, Any]:
        """Get cached weather data for a location.

        Args:
            location: Location identifier

        Returns:
            Weather data for the location
        """
        # Read from S3 cache
        try:
            key = f"weather-cache/{location}/latest.json"
            data = self.get_s3_object(self.config.input_bucket, key)
            import json

            return json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to get cached weather: {e}")
            raise
