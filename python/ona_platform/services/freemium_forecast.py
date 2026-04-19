"""Freemium Forecast client for Ona Platform SDK.

Wraps the public POST https://api.asoba.co/v1/freemium-forecast endpoint.
No API key required — accepts a CSV file of historical solar production data
and returns a 24-hour energy forecast.
"""

import logging
from pathlib import Path
from typing import Union

import requests

from ..exceptions import ValidationError, ServiceUnavailableError

logger = logging.getLogger(__name__)

FREEMIUM_FORECAST_URL = "https://api.asoba.co/v1/freemium-forecast"


class FreemiumForecastClient:
    """Client for the public Freemium Forecasting API.

    No API key required. Upload a CSV of historical solar production data
    and receive a 24-hour energy forecast.

    Example:
        >>> from ona_platform import OnaClient
        >>> client = OnaClient()
        >>> result = client.freemium_forecast.get_forecast(
        ...     csv_path="data.csv",
        ...     email="you@example.com",
        ...     site_name="My Solar Site",
        ...     location="Durban",
        ... )
        >>> for point in result["forecast"]["forecasts"]:
        ...     print(f"{point['timestamp']}: {point['kWh_forecast']} kWh")
    """

    def __init__(self, config=None):
        self._url = FREEMIUM_FORECAST_URL
        self._session = requests.Session()

    def get_forecast(
        self,
        csv_path: Union[str, Path],
        email: str,
        site_name: str,
        location: str,
    ) -> dict:
        """Generate a 24-hour solar energy forecast from a CSV file.

        Args:
            csv_path: Path to a CSV file with historical solar production data.
                      Must contain a timestamp column and a power/energy column.
            email: Your email address (used to identify requests).
            site_name: Descriptive name for the solar site.
            location: General location of the site (e.g. "Durban").

        Returns:
            dict with keys:
                - status: "success"
                - forecast.site_name
                - forecast.forecasts: list of {timestamp, hour_ahead, kWh_forecast, confidence}
                - forecast.summary: {total_kwh_24h, peak_hour, peak_kwh, average_hourly_kwh}

        Raises:
            ValidationError: CSV file not found, invalid email, or bad CSV format.
            ServiceUnavailableError: Server error or network failure.

        Example CSV format::

            Timestamp,Power (kW)
            2025-12-01T06:00:00Z,55.2
            2025-12-01T07:00:00Z,120.7
            2025-12-01T12:00:00Z,1850.2
        """
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise ValidationError(f"CSV file not found: {csv_path}")
        if not email or "@" not in email:
            raise ValidationError(f"Invalid email address: {email!r}")
        if not site_name:
            raise ValidationError("site_name is required")
        if not location:
            raise ValidationError("location is required")

        logger.debug(
            "freemium_forecast: site=%s location=%s file=%s",
            site_name, location, csv_path,
        )

        try:
            with open(csv_path, "rb") as f:
                resp = self._session.post(
                    self._url,
                    files={"file": (csv_path.name, f, "text/csv")},
                    data={
                        "email": email,
                        "site_name": site_name,
                        "location": location,
                    },
                    timeout=60,
                )
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Freemium forecast request failed: {e}") from e

        if resp.status_code == 400:
            body = resp.json() if resp.content else {}
            raise ValidationError(body.get("error", "Invalid request"))
        if resp.status_code >= 500:
            raise ServiceUnavailableError("Freemium forecast service unavailable")

        resp.raise_for_status()
        return resp.json()
