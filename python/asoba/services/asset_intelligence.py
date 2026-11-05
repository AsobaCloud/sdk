"""Asset intelligence service client (KPI rollups, soiling, prognostics)."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class AssetIntelligenceClient(BaseServiceClient):
    """Client for asset intelligence service."""

    def __init__(self, config: OnaConfig, function_name: str = "assetIntelligenceService"):
        super().__init__(config)
        self.function_name = function_name
        self._edge_endpoint = config.asset_intelligence_endpoint

    def run_all_sites(self) -> dict[str, Any]:
        """Run KPI/maintenance signal processing for all sites."""
        payload = {"source": "aws.events", "detail-type": "Scheduled Event"}
        logger.info("Running asset intelligence for all sites")
        if self.config.mode == "edge":
            return self._http_post(f"{self._edge_endpoint}/run", payload)
        return self.invoke_lambda(self.function_name, payload)

    def run_site(self, site_id: str, window_days: int = 30) -> dict[str, Any]:
        """Run KPI/maintenance signal processing for a single site."""
        payload = {
            "httpMethod": "POST",
            "path": "/api/kpi-rollup",
            "body": json.dumps({"site_id": site_id, "window_days": window_days}),
        }
        logger.info(f"Running asset intelligence for site: {site_id}")
        if self.config.mode == "edge":
            return self._http_post(
                f"{self._edge_endpoint}/api/kpi-rollup",
                {"site_id": site_id, "window_days": window_days},
            )
        return self.invoke_lambda(self.function_name, payload)
