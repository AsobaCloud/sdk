"""PVInsight service client (JEPA to RAG Nehanda synthesis)."""

from __future__ import annotations

import logging
from typing import Any

import requests

from ..config import OnaConfig
from ..exceptions import (
    ResourceNotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from ..utils import retry_with_backoff
from .base import BaseServiceClient

logger = logging.getLogger(__name__)


class PVInsightClient(BaseServiceClient):
    """Client for PVInsight service.

    Enriches JEPA anomaly detections with grounded O&M follow-up recommendations
    via an agentic tool loop over pgvector om_chunks and Nehanda LLM synthesis.
    """

    def __init__(self, config: OnaConfig, base_url: str | None = None):
        super().__init__(config)
        resolved_url = base_url or config.pvinsight_endpoint or "http://localhost:8003"
        self.base_url = resolved_url.rstrip("/")

    @retry_with_backoff(max_retries=3, backoff_factor=2.0)
    def analyze(
        self,
        detection: dict[str, Any],
        top_n: int = 5,
        min_severity: str = "minor",
        job_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyze a JEPA anomaly detection and generate grounded O&M recommendations.

        Args:
            detection: JEPA detection dictionary with asset_id, severity_label, etc.
            top_n: Number of retrieved knowledge chunks to consider.
            min_severity: Minimum severity threshold to trigger synthesis ("minor", "moderate", "critical").
            job_id: Optional async job ID for control-plane write-back.

        Returns:
            Detection payload enriched with llm_analysis.
        """
        if not detection:
            raise ValidationError("detection is required")

        url = f"{self.base_url}/analyze"
        payload: dict[str, Any] = {
            "detection": detection,
            "top_n": top_n,
            "min_severity": min_severity,
        }
        if job_id is not None:
            payload["job_id"] = job_id

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout,
            )

            if response.status_code == 400:
                error_detail = response.json().get("detail", "Validation error")
                raise ValidationError(str(error_detail))
            elif response.status_code == 404:
                error_detail = response.json().get("detail", "Resource not found")
                raise ResourceNotFoundError(str(error_detail))
            elif response.status_code >= 500:
                error_detail = response.json().get("detail", "Service error")
                raise ServiceUnavailableError(f"Service error: {error_detail}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise ServiceUnavailableError(
                f"Request timed out after {self.config.timeout}s"
            )
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Request failed: {e}")

    def health(self) -> dict[str, Any]:
        """Check service health."""
        url = f"{self.base_url}/health"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Health check failed: {e}")
