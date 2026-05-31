"""Data Standardization service client."""

import logging
from typing import Dict, Any

from .base import BaseServiceClient
from ..config import OnaConfig

logger = logging.getLogger(__name__)


class StandardizationClient(BaseServiceClient):
    """Client for Data Standardization service.

    Provides methods for data normalization and standardization.
    """

    def __init__(
        self,
        config: OnaConfig,
        function_name: str = "dataStandardizationService"
    ):
        """Initialize standardization client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for standardization service
        """
        super().__init__(config)
        self.function_name = function_name

    def standardize(
        self,
        customer_id: str,
        dataset_key: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Standardize dataset.

        Args:
            customer_id: Customer identifier
            dataset_key: S3 key for dataset to standardize
            **kwargs: Additional standardization parameters

        Returns:
            Standardization results
        """
        payload = {
            "customer_id": customer_id,
            "dataset_key": dataset_key,
            **kwargs
        }
        logger.info(f"Running standardization for customer: {customer_id}")
        return self.invoke_lambda(self.function_name, payload)
