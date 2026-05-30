"""Global Training service client."""

import logging
from typing import Any, Dict

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class TrainingClient(BaseServiceClient):
    """Client for Global Training service.

    Provides methods for ML model training and management operations.
    """

    def __init__(self, config: OnaConfig, function_name: str = "globalTrainingService"):
        """Initialize training client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for training service
        """
        super().__init__(config)
        self.function_name = function_name

    def trigger_training(
        self,
        customer_id: str,
        force: bool = False,
        promote: bool = False,
        test_only: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Trigger a model training job.

        Args:
            customer_id: Customer ID or 'generic'
            force: Force training if job already running
            promote: Auto-promote if validation passes
            test_only: Data prep only, no SageMaker training
            **kwargs: Additional parameters

        Returns:
            Job initiation results
        """
        payload = {
            "customer_id": customer_id,
            "force": force,
            "promote": promote,
            "test_only": test_only,
            **kwargs,
        }
        logger.info(f"Triggering training for customer: {customer_id}")
        return self.invoke_lambda(self.function_name, payload)

    def get_training_status(self, customer_id: str) -> Dict[str, Any]:
        """Get status of training job for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            Current status, progress, and metadata
        """
        # Note: Implementation might vary if status is a separate endpoint or action
        payload = {"action": "status", "customer_id": customer_id}
        logger.info(f"Getting training status for customer: {customer_id}")
        return self.invoke_lambda(self.function_name, payload)
