"""Data Ingestion service client."""

from __future__ import annotations

import logging
from typing import Any

from ..config import OnaConfig
from ..utils.validation import validate_batch
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

    def ingest(self, **kwargs) -> dict[str, Any]:
        """Trigger data ingestion process.

        Args:
            **kwargs: Ingestion parameters

        Returns:
            Ingestion status
        """
        payload = kwargs
        logger.info("Triggering data ingestion")
        return self.invoke_lambda(self.function_name, payload)

    def validate_local_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate records locally against ODSE schema without calling the service.

        Args:
            records: List of records to validate

        Returns:
            A dictionary containing valid_records, invalid_records, and a summary.
        """
        logger.info(f"Validating {len(records)} records locally")
        return validate_batch(records)
