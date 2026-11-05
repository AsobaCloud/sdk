"""Anomaly detection service client (LeWorldModel JEPA)."""

from __future__ import annotations

import logging
from typing import Any

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class AnomalyClient(BaseServiceClient):
    """Client for anomaly detection service.

    Provides methods for running JEPA world model anomaly detection
    on inverter telemetry data.
    """

    def __init__(self, config: OnaConfig, function_name: str = "anomalyModelService"):
        super().__init__(config)
        self.function_name = function_name
        self._edge_endpoint = config.anomaly_endpoint

    def detect(
        self,
        customer_id: str,
        asset_id: str,
        records: list[dict[str, Any]],
        rated_capacity_kw: float = 150.0,
    ) -> dict[str, Any]:
        """Run JEPA anomaly detection on inverter telemetry records."""
        payload = {
            "customer_id": customer_id,
            "asset_id": asset_id,
            "records": records,
            "rated_capacity_kw": rated_capacity_kw,
        }
        logger.info(f"Running anomaly detection for asset: {asset_id}")
        if self.config.mode == "edge":
            return self._http_post(f"{self._edge_endpoint}/detect", payload)
        return self.invoke_lambda(self.function_name, payload)

    def health(self) -> dict[str, Any]:
        """Check service health."""
        if self.config.mode == "edge":
            return self._http_get(f"{self._edge_endpoint}/health")
        return self.invoke_lambda(self.function_name, {"action": "health"})
