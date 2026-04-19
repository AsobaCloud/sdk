"""Global Training service client."""

import logging
from typing import Any, Dict, Optional

from ..config import OnaConfig
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class TrainingClient(BaseServiceClient):
    """Client for Global Training service.

    Provides methods for ML model training operations.
    """

    def __init__(self, config: OnaConfig, function_name: str = "globalTrainingService"):
        """Initialize training client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for training service
        """
        super().__init__(config)
        self.function_name = function_name

    def start_training(
        self,
        model_type: str,
        training_data_key: str,
        model_params: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Start model training job.

        Args:
            model_type: Type of model to train
            training_data_key: S3 key for training data
            model_params: Model hyperparameters
            **kwargs: Additional training parameters

        Returns:
            Training job information
        """
        payload = {
            "model_type": model_type,
            "training_data_key": training_data_key,
            "model_params": model_params or {},
            **kwargs,
        }
        logger.info(f"Starting training job for model type: {model_type}")
        return self.invoke_lambda(self.function_name, payload)

    def get_training_status(self, job_id: str) -> Dict[str, Any]:
        """Get status of training job.

        Args:
            job_id: Training job identifier

        Returns:
            Job status and metrics
        """
        payload = {"action": "status", "job_id": job_id}
        logger.info(f"Getting training status for job: {job_id}")
        return self.invoke_lambda(self.function_name, payload)

    def list_models(self) -> Dict[str, Any]:
        """List trained models.

        Returns:
            List of available models
        """
        payload = {"action": "list_models"}
        logger.info("Listing trained models")
        return self.invoke_lambda(self.function_name, payload)
