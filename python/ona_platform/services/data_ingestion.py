"""Data Ingestion service client."""

import logging
from typing import Any, Dict

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class DataIngestionClient(BaseServiceClient):
    """Client for Data Ingestion service.

    Provides methods for triggering data ingestion and preprocessing.
    """

    def __init__(self, config: OnaConfig, function_name: str = "dataIngestion"):
        """Initialize data ingestion client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for data ingestion service
        """
        super().__init__(config)
        self.function_name = function_name

    def ingest(self, **kwargs) -> Dict[str, Any]:
        """Trigger data ingestion process.

        Args:
            **kwargs: Ingestion parameters

        Returns:
            Ingestion status
        """
        payload = kwargs
        logger.info("Triggering data ingestion")
        return self.invoke_lambda(self.function_name, payload)
