"""Energy Analyst RAG service client."""

import logging
from typing import Dict, Any, List, Optional
import requests

from .base import BaseServiceClient
from ..config import OnaConfig
from ..exceptions import (
    ServiceUnavailableError,
    ValidationError,
    ResourceNotFoundError,
    ConfigurationError
)
from ..utils import retry_with_backoff

logger = logging.getLogger(__name__)


class EnergyAnalystClient(BaseServiceClient):
    """Client for EnergyAnalyst RAG service.

    Provides methods for querying energy policy documents and uploading PDFs.
    """

    def __init__(self, config: OnaConfig, base_url: Optional[str] = None):
        """Initialize Energy Analyst client.

        Args:
            config: SDK configuration
            base_url: Base URL for Energy Analyst service (overrides config)
        """
        super().__init__(config)
        self.base_url = base_url or config.energy_analyst_url

        if not self.base_url:
            raise ConfigurationError(
                "Energy Analyst URL not configured. Set ENERGY_ANALYST_URL "
                "environment variable or pass base_url parameter."
            )

    @retry_with_backoff(max_retries=3, backoff_factor=2.0)
    def query(
        self,
        question: str,
        n_results: int = 3,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """Query the RAG system with a question.

        Args:
            question: Question to ask about energy policies/regulations
            n_results: Number of context documents to retrieve (1-10)
            max_new_tokens: Maximum tokens to generate (50-2048)
            temperature: Sampling temperature (0.0-2.0)

        Returns:
            Answer with sources and citation

        Example:
            >>> result = client.energy_analyst.query(
            ...     "What are the grid code compliance requirements?",
            ...     n_results=3
            ... )
            >>> print(result['answer'])
            >>> print(result['citation'])
        """
        url = f"{self.base_url}/query"

        payload = {
            "question": question,
            "n_results": n_results
        }

        if max_new_tokens is not None:
            payload["max_new_tokens"] = max_new_tokens
        if temperature is not None:
            payload["temperature"] = temperature

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )

            if response.status_code == 400:
                error_detail = response.json().get('detail', 'Validation error')
                raise ValidationError(error_detail)
            elif response.status_code == 404:
                error_detail = response.json().get('detail', 'No relevant documents found')
                raise ResourceNotFoundError(error_detail)
            elif response.status_code >= 500:
                error_detail = response.json().get('detail', 'Service error')
                raise ServiceUnavailableError(f"Service error: {error_detail}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            raise ServiceUnavailableError(
                f"Request timed out after {self.config.timeout}s"
            )
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Request failed: {e}")

    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Add documents to the vector database.

        Args:
            texts: List of document texts to add
            metadatas: Optional metadata for each document

        Returns:
            Status and count of added documents

        Example:
            >>> result = client.energy_analyst.add_documents(
            ...     texts=["Document text 1", "Document text 2"],
            ...     metadatas=[
            ...         {"source": "doc1.pdf", "document_title": "Policy Doc 1"},
            ...         {"source": "doc2.pdf", "document_title": "Policy Doc 2"}
            ...     ]
            ... )
        """
        url = f"{self.base_url}/add_documents"

        payload = {"texts": texts}
        if metadatas:
            payload["metadatas"] = metadatas

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to add documents: {e}")

    def upload_pdfs(self, file_paths: List[str]) -> Dict[str, Any]:
        """Upload and process PDF files.

        Args:
            file_paths: List of paths to PDF files to upload

        Returns:
            Upload status and details

        Example:
            >>> result = client.energy_analyst.upload_pdfs([
            ...     "/path/to/policy1.pdf",
            ...     "/path/to/policy2.pdf"
            ... ])
        """
        url = f"{self.base_url}/upload_pdfs"

        files = []
        try:
            for path in file_paths:
                files.append(
                    ('files', (path.split('/')[-1], open(path, 'rb'), 'application/pdf'))
                )

            response = requests.post(
                url,
                files=files,
                timeout=self.config.timeout * 2  # PDFs may take longer
            )
            response.raise_for_status()
            return response.json()

        except FileNotFoundError as e:
            raise ValidationError(f"File not found: {e}")
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to upload PDFs: {e}")
        finally:
            for _, file_tuple in files:
                file_tuple[1].close()

    def health(self) -> Dict[str, Any]:
        """Check service health.

        Returns:
            Health status with model info and document count
        """
        url = f"{self.base_url}/health"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Health check failed: {e}")

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the document collection.

        Returns:
            Collection info with count and storage size
        """
        url = f"{self.base_url}/collection/info"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to get collection info: {e}")

    def clear_collection(self) -> Dict[str, Any]:
        """Clear all documents from the collection.

        Returns:
            Status message

        Warning:
            This operation cannot be undone!
        """
        url = f"{self.base_url}/collection/clear"

        try:
            response = requests.delete(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to clear collection: {e}")
