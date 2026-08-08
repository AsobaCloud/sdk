"""Terminal API client for OODA workflow operations."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any

import requests

from ..config import OnaConfig
from ..exceptions import AuthenticationError, ServiceUnavailableError
from ..models.intelligence import SiteSummary

logger = logging.getLogger(__name__)


class TerminalClient:
    """Client for the Terminal API (OODA workflow) at api.asoba.co/terminal/*.

    Obtains and caches a JWT from AuthClient automatically on first call.
    Call client.auth.login() once before using terminal methods.
    On 401, the token is refreshed and the request retried once.
    """

    def __init__(self, config: OnaConfig, auth_client=None):
        self.config = config
        self._auth_client = auth_client
        self._base_url = f"{config.terminal_endpoint.rstrip('/')}/terminal"
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def _get_token(self) -> str | None:
        """Return the current JWT from AuthClient, if available."""
        if self._auth_client is None:
            return None
        return self._auth_client.get_token()

    def _apply_auth(self):
        """Set Authorization header from the current token."""
        token = self._get_token()
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"
        elif "Authorization" in self._session.headers:
            del self._session.headers["Authorization"]

    def _post(self, path: str, body: dict) -> dict[str, Any]:
        """POST to /terminal/{path}, refreshing JWT on 401."""
        self._apply_auth()
        url = f"{self._base_url}/{path}"
        try:
            resp = self._session.post(url, json=body, timeout=self.config.timeout)
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Terminal API request failed: {e}") from e

        # On 401 try to refresh token once
        if resp.status_code == 401 and self._auth_client is not None:
            try:
                self._auth_client.refresh_token()
                self._apply_auth()
                resp = self._session.post(url, json=body, timeout=self.config.timeout)
            except Exception:
                pass

        if resp.status_code == 401:
            raise AuthenticationError(
                "Terminal API: unauthorized. Call client.auth.login() first."
            )
        if resp.status_code == 403:
            raise AuthenticationError(
                "Terminal API: forbidden. Token may lack access to this resource."
            )
        if resp.status_code >= 500:
            raise ServiceUnavailableError(
                f"Terminal API error {resp.status_code}: {resp.text}"
            )

        try:
            return resp.json()
        except Exception as e:
            raise ServiceUnavailableError(
                f"Terminal API returned non-JSON response: {e}"
            ) from e

    # ------------------------------------------------------------------
    # Asset Management
    # ------------------------------------------------------------------

    def list_assets(self, customer_id: str) -> list[dict[str, Any]]:
        """List all assets for a customer."""
        result = self._post("assets", {"action": "list", "customer_id": customer_id})
        return result.get("assets", [])

    def get_asset(self, customer_id: str, asset_id: str) -> dict[str, Any] | None:
        """Get a specific asset by ID. Returns None if not found."""
        result = self._post("assets", {
            "action": "get",
            "customer_id": customer_id,
            "asset_id": asset_id,
        })
        if result.get("statusCode") == 404:
            return None
        return result

    def add_asset(
        self,
        customer_id: str,
        asset_id: str,
        name: str,
        asset_type: str,
        capacity_kw: float,
        location: str,
        timezone: str = "Africa/Johannesburg",
        components: list[dict] | None = None,
        capacity_kwh: float | None = None,
        warranty_expiry_date: str | None = None,
        warranty_throughput_kwh: float | None = None,
    ) -> dict[str, Any]:
        """Add a new asset."""
        body: dict[str, Any] = {
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
        return self._post("assets", body)

    # ------------------------------------------------------------------
    # Detection (Observe)
    # ------------------------------------------------------------------

    def run_detection(
        self,
        customer_id: str,
        asset_id: str,
        lookback_hours: int = 6,
    ) -> dict[str, Any]:
        """Run ML-backed fault detection on an asset."""
        return self._post("detect", {
            "action": "run",
            "customer_id": customer_id,
            "asset_id": asset_id,
            "lookback_hours": lookback_hours,
        })

    def list_detections(self, customer_id: str) -> list[dict[str, Any]]:
        """List recent detections for a customer."""
        result = self._post("detect", {"action": "list", "customer_id": customer_id})
        return result.get("detections", [])

    def run_pv_insight_synthesis(
        self,
        detection: dict,
        user_query: str = "Analyze JEPA Anomaly & Recommend BOM",
    ) -> dict:
        """Delegate to pvInsightService for RAG + Nehanda synthesis on a detection."""
        return self._post("detect", {
            "action": "pv-insight",
            "detection": detection,
            "user_query": user_query,
        })

    # ------------------------------------------------------------------
    # Diagnostics (Orient)
    # ------------------------------------------------------------------

    def run_diagnostics(
        self,
        customer_id: str,
        asset_id: str,
        detection_id: str,
        lookback_hours: int = 6,
    ) -> dict[str, Any]:
        """Run AI diagnostics on a detected fault."""
        return self._post("diagnose", {
            "action": "run",
            "customer_id": customer_id,
            "asset_id": asset_id,
            "detection_id": detection_id,
            "lookback_hours": lookback_hours,
        })

    def list_diagnostics(self, customer_id: str) -> list[dict[str, Any]]:
        """List recent diagnostics for a customer."""
        result = self._post("diagnose", {"action": "list", "customer_id": customer_id})
        return result.get("diagnostics", [])

    # ------------------------------------------------------------------
    # Scheduling (Decide)
    # ------------------------------------------------------------------

    def create_schedule(
        self,
        customer_id: str,
        asset_id: str,
        description: str,
        priority: str = "Medium",
        estimated_duration_hours: int = 4,
        **kwargs,
    ) -> dict[str, Any]:
        """Create a maintenance schedule."""
        return self._post("schedule", {
            "action": "create",
            "customer_id": customer_id,
            "asset_id": asset_id,
            "description": description,
            "priority": priority,
            "estimated_duration_hours": estimated_duration_hours,
            **kwargs,
        })

    def list_schedules(self, customer_id: str) -> list[dict[str, Any]]:
        """List maintenance schedules for a customer."""
        result = self._post("schedule", {"action": "list", "customer_id": customer_id})
        return result.get("schedules", [])

    # ------------------------------------------------------------------
    # Issues Management
    # ------------------------------------------------------------------

    def list_issues(self, customer_id: str) -> list[dict[str, Any]]:
        """List issues for a customer."""
        result = self._post("issues", {"action": "list", "customer_id": customer_id})
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
    ) -> dict[str, Any]:
        """Create a new issue."""
        return self._post("issues", {
            "action": "create",
            "customer_id": customer_id,
            "component": component,
            "site": site,
            "issue_type": issue_type,
            "description": description,
            "priority": priority,
            **kwargs,
        })

    # ------------------------------------------------------------------
    # Activity Stream
    # ------------------------------------------------------------------

    def list_activities(self, customer_id: str) -> list[dict[str, Any]]:
        """List recent activities across all OODA phases."""
        result = self._post("activities", {"action": "list", "customer_id": customer_id})
        return result.get("activities", [])

    # ------------------------------------------------------------------
    # ML Integration
    # ------------------------------------------------------------------

    def get_forecast_results(self, customer_id: str) -> list[dict[str, Any]]:
        """Get ML forecast results for a customer."""
        result = self._post("forecast", {"customer_id": customer_id})
        return result.get("forecast_results", [])

    def get_interpolation_results(self, customer_id: str) -> list[dict[str, Any]]:
        """Get interpolation results for a customer."""
        result = self._post("interpolation", {"customer_id": customer_id})
        return result.get("interpolation_results", [])

    def get_ml_models(self) -> list[dict[str, Any]]:
        """Get ML model registry (shared across customers)."""
        result = self._post("ml-models", {})
        return result.get("model_metrics", [])

    def get_ml_ooda_summaries(self, customer_id: str) -> list[dict[str, Any]]:
        """Get ML-enhanced OODA summaries for a customer."""
        result = self._post("ooda", {"customer_id": customer_id})
        return result.get("ml_enhanced_activities", [])

    # ------------------------------------------------------------------
    # Site Summary & Nowcast
    # ------------------------------------------------------------------

    def get_site_summary(self, site_id: str) -> SiteSummary:
        """Get high-level site summary with KPIs and asset intelligence data."""
        result = self._post("telemetry", {"action": "site-summary", "site_id": site_id})
        return result.get("summary", {})

    def get_nowcast_data(
        self,
        customer_id: str,
        time_range: str = "1h",
        asset_filter: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get nowcast data for monitoring dashboard."""
        result = self._post("nowcastUI", {
            "action": "list",
            "customer_id": customer_id,
            "time_range": time_range,
            "asset_filter": asset_filter or [],
        })
        return result.get("data", {})

    # ------------------------------------------------------------------
    # Battery Health (static helper — no network call)
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_remaining_warranty_life(
        warranty_expiry_date: str | None,
        warranty_throughput_kwh: float | None,
        current_throughput_kwh: float | None = None,
    ) -> dict[str, Any]:
        """Calculate remaining warranty life for a battery asset.

        Returns:
            Dict with days_remaining, throughput_remaining_pct,
            warranty_status, and limiting_factor.
        """
        today = date.today()
        days_remaining = None
        throughput_remaining_pct = None
        date_status = "unknown"
        throughput_status = "unknown"

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
                days_remaining = None

        if warranty_throughput_kwh and current_throughput_kwh is not None and warranty_throughput_kwh > 0:
            remaining = max(0, warranty_throughput_kwh - current_throughput_kwh)
            throughput_remaining_pct = (remaining / warranty_throughput_kwh) * 100
            if current_throughput_kwh >= warranty_throughput_kwh:
                throughput_status = "out_of_warranty"
            elif current_throughput_kwh >= warranty_throughput_kwh * 0.8:
                throughput_status = "expiring_soon"
            else:
                throughput_status = "in_warranty"

        if date_status == "out_of_warranty" or throughput_status == "out_of_warranty":
            warranty_status = "out_of_warranty"
        elif date_status == "expiring_soon" or throughput_status == "expiring_soon":
            warranty_status = "expiring_soon"
        elif date_status == "in_warranty" or throughput_status == "in_warranty":
            warranty_status = "in_warranty"
        else:
            warranty_status = "unknown"

        if days_remaining is not None and throughput_remaining_pct is not None:
            limiting_factor = "throughput" if throughput_remaining_pct < 20 else "date"
        elif days_remaining is not None:
            limiting_factor = "date"
        elif throughput_remaining_pct is not None:
            limiting_factor = "throughput"
        else:
            limiting_factor = None

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
