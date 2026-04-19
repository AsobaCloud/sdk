"""Edge Device Registry service client."""

import logging
from typing import Dict, Any, List
import requests

from .base import BaseServiceClient
from ..config import OnaConfig
from ..exceptions import ServiceUnavailableError, ConfigurationError, ResourceNotFoundError

logger = logging.getLogger(__name__)


class EdgeDeviceClient(BaseServiceClient):
    """Client for Edge Device Registry service.

    Provides methods for device discovery, registration, and management.
    """

    def __init__(self, config: OnaConfig, base_url: str = None):
        """Initialize edge device client.

        Args:
            config: SDK configuration
            base_url: Base URL for edge device service (overrides config)
        """
        super().__init__(config)
        self.base_url = base_url or config.edge_api_url

        if not self.base_url:
            raise ConfigurationError(
                "Edge API URL not configured. Set EDGE_API_URL "
                "environment variable or pass base_url parameter."
            )

    def health(self) -> Dict[str, Any]:
        """Check service health."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Health check failed: {e}")

    def list_devices(self) -> List[Dict[str, Any]]:
        """Get all registered devices."""
        try:
            response = requests.get(f"{self.base_url}/api/devices", timeout=self.config.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to list devices: {e}")

    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get specific device by ID."""
        try:
            response = requests.get(
                f"{self.base_url}/api/devices/{device_id}", timeout=self.config.timeout
            )
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Device not found: {device_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to get device: {e}")

    def discover_device(self, ip: str, username: str) -> Dict[str, Any]:
        """Discover and register a new device."""
        try:
            response = requests.post(
                f"{self.base_url}/api/devices",
                json={"ip": ip, "username": username},
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Device discovery failed: {e}")

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update device information."""
        try:
            response = requests.put(
                f"{self.base_url}/api/devices/{device_id}",
                json=updates,
                timeout=self.config.timeout,
            )
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Device not found: {device_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to update device: {e}")

    def delete_device(self, device_id: str) -> Dict[str, Any]:
        """Delete device from registry."""
        try:
            response = requests.delete(
                f"{self.base_url}/api/devices/{device_id}", timeout=self.config.timeout
            )
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Device not found: {device_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to delete device: {e}")

    def get_device_capabilities(self, device_id: str) -> Dict[str, Any]:
        """Get device capabilities."""
        try:
            response = requests.get(
                f"{self.base_url}/api/devices/{device_id}/capabilities", timeout=self.config.timeout
            )
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Device not found: {device_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to get capabilities: {e}")

    def get_device_services(self, device_id: str) -> List[Dict[str, Any]]:
        """Get services running on device."""
        try:
            response = requests.get(
                f"{self.base_url}/api/devices/{device_id}/services", timeout=self.config.timeout
            )
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Device not found: {device_id}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Failed to get services: {e}")
