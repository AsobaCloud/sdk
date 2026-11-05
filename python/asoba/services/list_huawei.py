"""List Huawei customers service client."""

from __future__ import annotations

import logging
from typing import Any

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class ListHuaweiCustomersClient(BaseServiceClient):
    """Client for Huawei customer/plant discovery service."""

    def __init__(self, config: OnaConfig, function_name: str = "listHuaweiCustomersService"):
        super().__init__(config)
        self.function_name = function_name
        self._edge_endpoint = config.list_huawei_customers_endpoint

    def list_customers(self, manufacturer: str = "Huawei") -> dict[str, Any]:
        """List Huawei customers and plants from the assets table."""
        payload = {"manufacturer": manufacturer}
        logger.info(f"Listing Huawei customers (manufacturer={manufacturer})")
        if self.config.mode == "edge":
            return self._http_post(f"{self._edge_endpoint}/run", payload)
        return self.invoke_lambda(self.function_name, payload)
