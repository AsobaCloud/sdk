"""Terminal API client for OODA workflow operations."""

import json
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from ..config import OnaConfig
from ..exceptions import ResourceNotFoundError
from .base import BaseServiceClient

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
            List of asset objects. Battery assets include capacity_kwh,
            warranty_expiry_date, and warranty_throughput_kwh fields.
        """
        payload = {
            "httpMethod": "POST",
            "path": "/assets",
            "body": json.dumps({"action": "list", "customer_id": customer_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result.get("assets", [])

    def get_asset(self, customer_id: str, asset_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific asset by ID.

        Args:
            customer_id: Customer identifier
            asset_id: Asset identifier

        Returns:
            Asset object including battery-specific fields (capacity_kwh,
            warranty_expiry_date, warranty_throughput_kwh) if present.
            Returns None if asset not found.
        """
        payload = {
            "httpMethod": "POST",
            "path": "/assets",
            "body": json.dumps(
                {"action": "get", "customer_id": customer_id, "asset_id": asset_id}
            ),
        }
        try:
            result = self.invoke_lambda(self.function_name, payload)
            return result
        except ResourceNotFoundError:
            return None

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
        capacity_kwh: Optional[float] = None,
        warranty_expiry_date: Optional[str] = None,
        warranty_throughput_kwh: Optional[float] = None,
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
            capacity_kwh: Optional battery capacity in kWh
            warranty_expiry_date: Optional warranty expiry date (YYYY-MM-DD)
            warranty_throughput_kwh: Optional warranty throughput limit in kWh

        Returns:
            Created asset information
        """
        body = {
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
        if capacity_kwh is not None:
            body["capacity_kwh"] = capacity_kwh
        if warranty_expiry_date:
            body["warranty_expiry_date"] = warranty_expiry_date
        if warranty_throughput_kwh is not None:
            body["warranty_throughput_kwh"] = warranty_throughput_kwh

        payload = {
            "httpMethod": "POST",
            "path": "/assets",
            "body": json.dumps(body),
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

    # Telemetry
    def get_site_summary(self, site_id: str) -> Dict[str, Any]:
        """Get site summary including battery KPIs from assetIntelligence snapshots.

        Args:
            site_id: Site identifier

        Returns:
            Site summary with fleet metrics and battery KPIs (avg_soc, avg_soh,
            total_capacity_kwh, warranty_status) if available.
        """
        payload = {
            "httpMethod": "POST",
            "path": "/telemetry",
            "body": json.dumps({"action": "site-summary", "site_id": site_id}),
        }
        result = self.invoke_lambda(self.function_name, payload)
        return result

    # Battery Health Helper Methods
    @staticmethod
    def calculate_remaining_warranty_life(
        warranty_expiry_date: Optional[str],
        warranty_throughput_kwh: Optional[float],
        current_throughput_kwh: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Calculate remaining warranty life for a battery asset.

        Args:
            warranty_expiry_date: Warranty expiry date in ISO format (YYYY-MM-DD)
            warranty_throughput_kwh: Total warranty throughput limit in kWh
            current_throughput_kwh: Current cumulative throughput in kWh (optional)

        Returns:
            Dict with keys:
            - days_remaining: Days until date-based warranty expiry (None if no date)
            - throughput_remaining_pct: Percentage of throughput warranty remaining (None if no limit)
            - warranty_status: 'in_warranty', 'expiring_soon', 'out_of_warranty', or 'unknown'
            - limiting_factor: 'date' or 'throughput' indicating which constraint is tighter
        """
        today = date.today()
        days_remaining = None
        throughput_remaining_pct = None
        warranty_status = "unknown"
        limiting_factor = None

        # Check date-based warranty
        if warranty_expiry_date:
            try:
                expiry = datetime.strptime(warranty_expiry_date, "%Y-%m-%d").date()
                days_remaining = (expiry - today).days
                if days_remaining < 0:
                    date_status = "out_of_warranty"
                elif days_remaining < 90:
                    date_status = "expiring_soon"
                else:
                    date_status = "in_warranty"
            except (ValueError, TypeError):
                date_status = "unknown"
                days_remaining = None
        else:
            date_status = "unknown"

        # Check throughput-based warranty
        if warranty_throughput_kwh and current_throughput_kwh is not None:
            if warranty_throughput_kwh > 0:
                throughput_remaining = max(
                    0, warranty_throughput_kwh - current_throughput_kwh
                )
                throughput_remaining_pct = (
                    throughput_remaining / warranty_throughput_kwh
                ) * 100
                if current_throughput_kwh >= warranty_throughput_kwh:
                    throughput_status = "out_of_warranty"
                elif current_throughput_kwh >= warranty_throughput_kwh * 0.8:
                    throughput_status = "expiring_soon"
                else:
                    throughput_status = "in_warranty"
            else:
                throughput_status = "unknown"
        else:
            throughput_status = "unknown"

        # Determine overall warranty status (worst of the two)
        if date_status == "out_of_warranty" or throughput_status == "out_of_warranty":
            warranty_status = "out_of_warranty"
        elif date_status == "expiring_soon" or throughput_status == "expiring_soon":
            warranty_status = "expiring_soon"
        elif date_status == "in_warranty" or throughput_status == "in_warranty":
            warranty_status = "in_warranty"

        # Determine limiting factor
        if days_remaining is not None and throughput_remaining_pct is not None:
            # Compare days remaining vs throughput remaining
            # Simple heuristic: if throughput is < 20% remaining, it's the limiting factor
            if throughput_remaining_pct < 20:
                limiting_factor = "throughput"
            elif days_remaining < 90:
                limiting_factor = "date"
            else:
                limiting_factor = "date"  # Default to date as primary
        elif days_remaining is not None:
            limiting_factor = "date"
        elif throughput_remaining_pct is not None:
            limiting_factor = "throughput"

        return {
            "days_remaining": days_remaining,
            "throughput_remaining_pct": (
                round(throughput_remaining_pct, 1)
                if throughput_remaining_pct is not None
                else None
            ),
            "warranty_status": warranty_status,
            "limiting_factor": limiting_factor,
        }
