"""Gap Detection service client."""

import logging
from typing import Any, Dict, Optional

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class GapDetectionClient(BaseServiceClient):
    """Client for Gap Detection service.

    Identifies missing data intervals and triggers targeted backfill.
    """

    def __init__(self, config: OnaConfig, function_name: str = "gapDetectionService"):
        """Initialize gap detection client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for gap detection service
        """
        super().__init__(config)
        self.function_name = function_name

    def detect_gaps(
        self,
        customer_id: str,
        client_id: str = "asoba",
        region: str = "af-south-1",
        location: str = "Durban",
        manufacturer: str = "Huawei",
        lookback_days: int = 7,
        min_gap_minutes: int = 15,
        **kwargs,
    ) -> Dict[str, Any]:
        """Run gap detection scan.

        Args:
            customer_id: Customer identifier
            client_id: Client identifier
            region: AWS region
            location: Site location
            manufacturer: Device manufacturer
            lookback_days: Number of days to look back
            min_gap_minutes: Minimum gap size to report
            **kwargs: Additional parameters

        Returns:
            Detection results with gaps and backfill targets
        """
        payload = {
            "customer_id": customer_id,
            "client_id": client_id,
            "region": region,
            "location": location,
            "manufacturer": manufacturer,
            "lookback_days": lookback_days,
            "min_gap_minutes": min_gap_minutes,
            **kwargs,
        }
        logger.info(f"Running gap detection for customer: {customer_id}")
        return self.invoke_lambda(self.function_name, payload)
