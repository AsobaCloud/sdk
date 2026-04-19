"""Interpolation service client."""

import logging
from typing import Dict, Any

from .base import BaseServiceClient
from ..config import OnaConfig

logger = logging.getLogger(__name__)


class InterpolationClient(BaseServiceClient):
    """Client for Interpolation service.

    Provides methods for data interpolation and gap filling.
    """

    def __init__(self, config: OnaConfig, function_name: str = "interpolationService"):
        """Initialize interpolation client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for interpolation service
        """
        super().__init__(config)
        self.function_name = function_name

    def interpolate(self, customer_id: str, dataset_key: str, **kwargs) -> Dict[str, Any]:
        """Interpolate missing data points.

        Args:
            customer_id: Customer identifier
            dataset_key: S3 key for dataset to interpolate
            **kwargs: Additional interpolation parameters

        Returns:
            Interpolation results
        """
        payload = {"customer_id": customer_id, "dataset_key": dataset_key, **kwargs}
        logger.info(f"Running interpolation for customer: {customer_id}")
        return self.invoke_lambda(self.function_name, payload)
