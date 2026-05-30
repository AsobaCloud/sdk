"""Freemium Forecast client for Ona Platform SDK.

Wraps the two-step verify+forecast API at https://forecasting.api.asoba.org.
No API key required — accepts a CSV file of historical solar production data
and returns a 24-hour energy forecast.
"""

import logging
from pathlib import Path
from typing import Union

import requests

from ..exceptions import ServiceUnavailableError, ValidationError

logger = logging.getLogger(__name__)

FREEMIUM_BASE_URL = "https://forecasting.api.asoba.org"

_VERIFY_PATH = "/api/v1/freemium-forecast/verify"
_FORECAST_PATH = "/api/v1/freemium-forecast"


class FreemiumForecastClient:
    """Client for the public Freemium Forecasting API.

    No API key required. Use request_verification_code() to obtain a one-time
    code, then call get_forecast() with that code to receive a 24-hour energy
    forecast.

    Example:
        >>> from ona_platform import OnaClient
        >>> client = OnaClient()
        >>> client.freemium_forecast.request_verification_code(email="you@example.com")
        >>> result = client.freemium_forecast.get_forecast(
        ...     csv_path="data.csv",
        ...     email="you@example.com",
        ...     verification_code="123456",
        ...     site_name="My Solar Site",
        ...     location="Durban",
        ...     capacity_kw=500.0,
        ... )
        >>> for point in result["forecast"]["forecasts"]:
        ...     print(f"{point['timestamp']}: {point['kWh_forecast']} kWh")
    """

    def __init__(self, config=None):
        self._base_url = FREEMIUM_BASE_URL
        self._session = requests.Session()

    def request_verification_code(self, email: str) -> dict:
        """Request a one-time verification code to be sent to the given email.

        Args:
            email: The email address to send the verification code to.

        Returns:
            dict with the server response (e.g. {"status": "success", "message": "..."}).

        Raises:
            ValidationError: Server returned HTTP 400.
            ServiceUnavailableError: Server error or network failure.
        """
        url = self._base_url + _VERIFY_PATH
        try:
            resp = self._session.post(
                url,
                json={"email": email},
                timeout=30,
            )
        except requests.exceptions.RequestException as e:
            raise ServiceUnavailableError(f"Verification request failed: {e}") from e

        if resp.status_code == 400:
            body = resp.json() if resp.content else {}
            raise ValidationError(body.get("error", "Invalid request"))
        if resp.status_code >= 500:
            raise ServiceUnavailableError("Freemium forecast service unavailable")

        resp.raise_for_status()
        return resp.json()

    def get_forecast(
        self,
        csv_path: Union[str, Path],
        email: str,
        verification_code: str,
        site_name: str,
        location: str,
        capacity_kw: float,
        tou_accepted: bool = False,
        marketing_opt_in: bool = False,
    ) -> dict:
        """Generate a 24-hour solar energy forecast from a CSV file.

        Args:
            csv_path: Path to a CSV file with historical solar production data.
                      Must contain a timestamp column and a power/energy column.
            email: Your email address (used to identify requests).
            verification_code: One-time code received via request_verification_code().
            site_name: Descriptive name for the solar site.
            location: General location of the site (e.g. "Durban").
            capacity_kw: Installed capacity of the solar installation in kW.

        Returns:
            dict with keys:
                - status: "success"
                - forecast.site_name
                - forecast.forecasts: list of {timestamp, kWh_forecast}
                - forecast.summary: {total_kwh_24h, ...}

        Raises:
            ValidationError: CSV file not found, invalid email, missing fields,
                             or server returned HTTP 400.
            ServiceUnavailableError: Server error or network failure.

        Example CSV format::

            Timestamp,Power (kW)
            2025-12-01T06:00:00Z,55.2
            2025-12-01T07:00:00Z,120.7
            2025-12-01T12:00:00Z,1850.2
        """
        if not tou_accepted:
            raise ValidationError(
                "You must accept the Terms of Use (tou_accepted=True) to use this service."
            )
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
            "freemium_forecast: site=%s location=%s capacity_kw=%s file=%s",
            site_name,
            location,
            capacity_kw,
            csv_path,
        )

        url = self._base_url + _FORECAST_PATH
        try:
            with open(csv_path, "rb") as f:
                resp = self._session.post(
                    url,
                    files={"file": (csv_path.name, f, "text/csv")},
                    data={
                        "email": email,
                        "verification_code": verification_code,
                        "site_name": site_name,
                        "location": location,
                        "capacity_kw": str(capacity_kw),
                        "tou_accepted": "true",
                        "marketing_opt_in": "true" if marketing_opt_in else "false",
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
