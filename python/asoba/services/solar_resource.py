"""Solar resource service client (P50/P90 PSH yield estimation)."""

from __future__ import annotations

import logging
from typing import Any

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class SolarResourceClient(BaseServiceClient):
    """Client for solar resource service."""

    def __init__(self, config: OnaConfig, function_name: str = "solarResourceService"):
        super().__init__(config)
        self.function_name = function_name
        self._edge_endpoint = config.solar_resource_endpoint

    def get_p50_p90(self, lat: float, lon: float) -> dict[str, Any]:
        """Get P50/P90 peak sun hours for a location."""
        logger.info(f"Getting P50/P90 for lat={lat}, lon={lon}")
        if self.config.mode == "edge":
            return self._http_get(
                f"{self._edge_endpoint}/api/v1/solar-resource",
                params={"lat": lat, "lon": lon},
            )
        payload = {
            "httpMethod": "GET",
            "queryStringParameters": {"lat": str(lat), "lon": str(lon)},
        }
        return self.invoke_lambda(self.function_name, payload)

    def refresh_index(self) -> dict[str, Any]:
        """Rebuild P50/P90 index."""
        logger.info("Refreshing P50/P90 index")
        if self.config.mode == "edge":
            return self._http_post(f"{self._edge_endpoint}/refresh-index", {})
        payload = {"source": "aws.events", "detail-type": "Scheduled Event"}
        return self.invoke_lambda(self.function_name, payload)
