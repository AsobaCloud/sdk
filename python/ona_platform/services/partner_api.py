"""Partner API client for Ona Platform SDK."""

import logging
from typing import Dict, Optional

import requests

from ..config import OnaConfig
from ..exceptions import (
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
    ServiceUnavailableError,
)


class PartnerApiClient:
    """Client for the Partner API.

    Provides access to pre-computed JSON snapshots with ETag-based caching.
    """

    def __init__(self, config: OnaConfig):
        if not config.partner_api_endpoint:
            raise ConfigurationError("partner_api_endpoint is required")
        if not config.partner_api_endpoint.startswith("https://"):
            raise ConfigurationError("partner_api_endpoint must use https://")
        if not config.partner_api_key:
            raise AuthenticationError("partner_api_key is required")

        self._endpoint = config.partner_api_endpoint.rstrip("/")
        self._api_key = config.partner_api_key
        self._session = requests.Session()
        self._session.headers.update(
            {
                "x-api-key": self._api_key,
                "Accept": "application/json",
                "User-Agent": "ona-platform-sdk-python/1.1.0",
            }
        )
        self._etag_cache: Dict[str, Dict] = {}  # url -> {etag, data}
        self._logger = logging.getLogger(__name__)

    def _request(self, path: str, params: dict):
        base_url = f"{self._endpoint}{path}"
        # Prepare request to get the full URL with query parameters for caching
        prep = requests.Request("GET", base_url, params=params).prepare()
        full_url = prep.url
        if full_url is None:
            full_url = base_url

        headers = {}
        cached = self._etag_cache.get(full_url)
        if cached:
            headers["If-None-Match"] = cached["etag"]

        try:
            resp = self._session.get(full_url, headers=headers, timeout=30)

            if resp.status_code == 304 and cached:
                self._logger.debug("ETag match for %s, serving from cache", full_url)
                return cached["data"]

            if resp.status_code in (401, 403):
                raise AuthenticationError(f"Access denied: {resp.text}")
            if resp.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            if resp.status_code >= 500:
                raise ServiceUnavailableError(f"Service unavailable: {resp.status_code}")

            resp.raise_for_status()
            data = resp.json()

            etag = resp.headers.get("ETag")
            if etag:
                self._etag_cache[full_url] = {"etag": etag, "data": data}

            return data
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Request failed: {e}") from e

    def get_kpi_rollup(self, site_id: str) -> dict:
        """Get the latest KPI Rollup snapshot for a site.

        The KPI rollup includes energy balance, performance, availability,
        financial metrics, and battery health KPIs (avg_soc, avg_soh,
        total_capacity_kwh, warranty_status, throughput_kwh, etc.) for sites
        with battery assets.
        """
        return self._request("/kpi-rollup", {"site_id": site_id})

    def get_maintenance_signals(
        self,
        site_id: str,
        since: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> dict:
        """Get maintenance signals for a site."""
        params = {"site_id": site_id}
        if since:
            params["since"] = since
        if severity:
            params["severity"] = severity
        return self._request("/maintenance-signals", params)

    def get_forecast_snapshot(self, site_id: str, horizon: Optional[str] = None) -> dict:
        """Get the latest forecast snapshot for a site."""
        params = {"site_id": site_id}
        if horizon:
            params["horizon"] = horizon
        return self._request("/forecast-snapshot", params)

    def get_maintenance_schedule(
        self,
        site_id: str,
        since: Optional[str] = None,
    ) -> dict:
        """Get the preventive-maintenance schedule snapshot for a site.

        Returns a forward-looking 90-day task list grouped by inverter,
        derived from rolling-window anomaly frequency and configurable
        manufacturer service intervals. Companion to maintenance-signals
        (which reports detected anomalies). See SEP-062.
        """
        params = {"site_id": site_id}
        if since:
            params["since"] = since
        return self._request("/maintenance-schedule", params)

    def get_snapshot(self, site_id: str, kind: str, **kwargs) -> dict:
        """Get a generic snapshot for a site."""
        params = {"site_id": site_id, "kind": kind}
        params.update(kwargs)
        return self._request("/snapshot", params)
