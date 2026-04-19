"""Terminal API client for OODA workflow operations."""

import json
import logging
from typing import Dict, Any, List, Optional

from .base import BaseServiceClient
from ..config import OnaConfig

logger = logging.getLogger(__name__)


class TerminalClient(BaseServiceClient):
    """Client for Terminal API - OODA workflow operations.

    Provides methods for:
    - Asset management
    - Fault detection (Observe)
    - AI diagnostics (Orient)
    - Maintenance scheduling (Decide)
    - BOM generation and work orders (Act)
    - Activity tracking
    - Issues management
    - ML integration (forecasts, interpolation, model registry, OODA summaries)
    """

    def __init__(self, config: OnaConfig, function_name: str = "terminalApi"):
        """Initialize terminal client.

        Args:
            config: SDK configuration
            function_name: Lambda function name for terminal service
        """
        super().__init__(config)
        self.function_name = function_name

    # Asset Management
    def list_assets(self, customer_id: str) -> List[Dict[str, Any]]:
        """List all assets for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of asset objects
        """
        payload = {
            "httpMethod": "POST",
            "path": "/assets",
            "body": json.dumps({"action": "list", "customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("assets", [])

    def add_asset(
        self,
        customer_id: str,
        asset_id: str,
        name: str,
        asset_type: str,
        capacity_kw: float,
        location: str,
        timezone: str = "Africa/Johannesburg",
        components: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """Add a new asset.

        Args:
            customer_id: Customer identifier
            asset_id: Unique asset identifier
            name: Asset name
            asset_type: Asset type (e.g., 'solar', 'inverter')
            capacity_kw: Capacity in kilowatts
            location: Asset location
            timezone: Asset timezone (default: Africa/Johannesburg)
            components: Optional list of asset components

        Returns:
            Created asset information
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/assets",
            "body": json.dumps(
                {
                    "action": "add",
                    "customer_id": customer_id,
                    "asset_id": asset_id,
                    "name": name,
                    "type": asset_type,
                    "capacity_kw": capacity_kw,
                    "location": location,
                    "timezone": timezone,
                    "components": components or [],
                }
            ),
        }
        return self.invoke_lambda(self.function_name, payload)

    # Detection (Observe)
    def run_detection(
        self, customer_id: str, asset_id: str, lookback_hours: int = 6
    ) -> Dict[str, Any]:
        """Run ML-backed fault detection on an asset.

        Args:
            customer_id: Customer identifier
            asset_id: Asset identifier
            lookback_hours: Hours of historical data to analyze (1-24)

        Returns:
            Detection analysis with severity, fault type, and metrics
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/detect",
            "body": json.dumps(
                {
                    "action": "run",
                    "customer_id": customer_id,
                    "asset_id": asset_id,
                    "lookback_hours": lookback_hours,
                }
            ),
        }
        return self.invoke_lambda(self.function_name, payload)

    def list_detections(self, customer_id: str) -> List[Dict[str, Any]]:
        """List recent detections for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of detection records
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/detect",
            "body": json.dumps({"action": "list", "customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("detections", [])

    # Diagnostics (Orient)
    def run_diagnostics(
        self, customer_id: str, asset_id: str, detection_id: str, lookback_hours: int = 6
    ) -> Dict[str, Any]:
        """Run AI diagnostics on a detected fault.

        Args:
            customer_id: Customer identifier
            asset_id: Asset identifier
            detection_id: Detection ID to diagnose
            lookback_hours: Hours of historical data to analyze

        Returns:
            Diagnostic analysis with root cause and recommended actions
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/diagnose",
            "body": json.dumps(
                {
                    "action": "run",
                    "customer_id": customer_id,
                    "asset_id": asset_id,
                    "detection_id": detection_id,
                    "lookback_hours": lookback_hours,
                }
            ),
        }
        return self.invoke_lambda(self.function_name, payload)

    def list_diagnostics(self, customer_id: str) -> List[Dict[str, Any]]:
        """List recent diagnostics for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of diagnostic records
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/diagnose",
            "body": json.dumps({"action": "list", "customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("diagnostics", [])

    # Scheduling (Decide)
    def create_schedule(
        self,
        customer_id: str,
        asset_id: str,
        description: str,
        priority: str = "Medium",
        estimated_duration_hours: int = 4,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a maintenance schedule.

        Args:
            customer_id: Customer identifier
            asset_id: Asset identifier
            description: Schedule description
            priority: Priority level (Low, Medium, High)
            estimated_duration_hours: Estimated duration in hours
            **kwargs: Additional schedule fields

        Returns:
            Created schedule information
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/schedule",
            "body": json.dumps(
                {
                    "action": "create",
                    "customer_id": customer_id,
                    "asset_id": asset_id,
                    "description": description,
                    "priority": priority,
                    "estimated_duration_hours": estimated_duration_hours,
                    **kwargs,
                }
            ),
        }
        return self.invoke_lambda(self.function_name, payload)

    def list_schedules(self, customer_id: str) -> List[Dict[str, Any]]:
        """List maintenance schedules for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of schedule records
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/schedule",
            "body": json.dumps({"action": "list", "customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("schedules", [])

    # Issues Management
    def list_issues(self, customer_id: str) -> List[Dict[str, Any]]:
        """List issues for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of issue records
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/issues",
            "body": json.dumps({"action": "list", "customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("issues", [])

    def create_issue(
        self,
        customer_id: str,
        component: str,
        site: str,
        issue_type: str,
        description: str,
        priority: str = "Medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a new issue.

        Args:
            customer_id: Customer identifier
            component: Component name
            site: Site name
            issue_type: Type of issue
            description: Issue description
            priority: Priority level
            **kwargs: Additional issue fields

        Returns:
            Created issue information
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/issues",
            "body": json.dumps(
                {
                    "action": "create",
                    "customer_id": customer_id,
                    "component": component,
                    "site": site,
                    "issue_type": issue_type,
                    "description": description,
                    "priority": priority,
                    **kwargs,
                }
            ),
        }
        return self.invoke_lambda(self.function_name, payload)

    # Activity Stream
    def list_activities(self, customer_id: str) -> List[Dict[str, Any]]:
        """List recent activities across all OODA phases.

        Args:
            customer_id: Customer identifier

        Returns:
            List of activity records from last 24 hours
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/activities",
            "body": json.dumps({"action": "list", "customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("activities", [])

    # ML Integration
    def get_forecast_results(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get ML forecast results for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of recent forecast results
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/forecast",
            "body": json.dumps({"customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("forecast_results", [])

    def get_interpolation_results(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get interpolation results for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of recent interpolation results
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/interpolation",
            "body": json.dumps({"customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("interpolation_results", [])

    def get_ml_models(self) -> List[Dict[str, Any]]:
        """Get ML model registry (shared across customers).

        Returns:
            List of registered models with training metrics
        """
        import json

        payload = {"httpMethod": "POST", "path": "/ml-models", "body": json.dumps({})}
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("model_metrics", [])

    def get_ml_ooda_summaries(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get ML-enhanced OODA summaries for a customer.

        Args:
            customer_id: Customer identifier

        Returns:
            List of ML-enhanced OODA activities
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/ooda",
            "body": json.dumps({"customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("ml_enhanced_activities", [])

    # Nowcast UI Data
    def get_nowcast_data(
        self, customer_id: str, time_range: str = "1h", asset_filter: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get nowcast data for monitoring dashboard.

        Args:
            customer_id: Customer identifier
            time_range: Time range ('1h', '6h', '24h', '7d', 'latest')
            asset_filter: Optional list of asset IDs to filter

        Returns:
            Nowcast data with latest metrics and time series
        """
        import json

        payload = {
            "httpMethod": "POST",
            "path": "/nowcastUI",
            "body": json.dumps(
                {
                    "action": "list",
                    "customer_id": customer_id,
                    "time_range": time_range,
                    "asset_filter": asset_filter or [],
                }
            ),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("data", {})
