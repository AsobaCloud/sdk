"""OODA Terminal client for Ona Platform SDK."""

import logging
import time
from typing import Dict, Generator, List, Optional

import requests

from ..config import OnaConfig
from ..exceptions import (
    AuthenticationError,
    ConfigurationError,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)
from ..models.ooda import DataPeriod, OodaAlert, TimeRange
from .ooda_cursor import OodaCursorSerializer

MAX_LIMIT = 1000
MIN_POLLING_INTERVAL = 5.0
MAX_TIME_RANGE_DAYS = 31


class OodaTerminalClient:
    def __init__(self, config: OnaConfig):
        if not config.ooda_terminal_endpoint:
            raise ConfigurationError("ooda_terminal_endpoint is required")
        if not config.ooda_terminal_endpoint.startswith("https://"):
            raise ConfigurationError("ooda_terminal_endpoint must use https://")
        if not config.ooda_terminal_api_key:
            raise AuthenticationError("ooda_terminal_api_key is required")
        self._endpoint = config.ooda_terminal_endpoint.rstrip("/")
        self._api_key = config.ooda_terminal_api_key
        self._polling_interval = config.ooda_polling_interval
        self._max_retries = config.max_retries
        self._session = requests.Session()
        self._session.headers.update({"x-api-key": self._api_key})
        self._active_streams: set = set()
        self._logger = logging.getLogger(__name__)

    def _validate_query_params(self, site_id: str, time_range: TimeRange, limit: int):
        from datetime import datetime, timezone

        if not site_id:
            raise ValidationError("site_id is required")
        if time_range.start > time_range.end:
            raise ValidationError(
                f"time_range.start must be <= time_range.end (got start={time_range.start!r}, end={time_range.end!r})"
            )
        if limit > MAX_LIMIT:
            raise ValidationError(f"limit must not exceed {MAX_LIMIT} (got {limit})")

        def _parse_dt(s):
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt

        start_dt = _parse_dt(time_range.start)
        end_dt = _parse_dt(time_range.end)
        if (end_dt - start_dt).days > MAX_TIME_RANGE_DAYS:
            raise ValidationError(f"time_range span must not exceed {MAX_TIME_RANGE_DAYS} days")

    def _handle_response(self, response, operation: str, identifier: str):
        if response.status_code in (401, 403):
            raise AuthenticationError(f"{operation} for {identifier}: access denied")
        if response.status_code == 429:
            raise RateLimitError(f"{operation} for {identifier}: rate limit exceeded")
        if response.status_code >= 500:
            raise ServiceUnavailableError(f"{operation} for {identifier}: service unavailable")
        response.raise_for_status()
        return response.json()

    def _get_with_retry(self, url: str, params: dict, operation: str, identifier: str):
        for attempt in range(1, self._max_retries + 2):
            try:
                resp = self._session.get(url, params=params, timeout=30)
                if resp.status_code >= 500 and attempt <= self._max_retries:
                    self._logger.warning(
                        "%s attempt %d failed with %d", operation, attempt, resp.status_code
                    )
                    time.sleep(2 ** (attempt - 1))
                    continue
                return self._handle_response(resp, operation, identifier)
            except (AuthenticationError, RateLimitError, ValidationError):
                raise
            except requests.exceptions.RequestException as e:
                if attempt <= self._max_retries:
                    time.sleep(2 ** (attempt - 1))
                    continue
                raise ServiceUnavailableError(f"{operation} failed: {e}") from e
        raise ServiceUnavailableError(
            f"{operation} for {identifier}: service unavailable after retries"
        )

    def get_terminal_alerts(
        self,
        terminal_device_id: str,
        site_id: str,
        time_range: TimeRange,
        resolution: str = "5min",
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> List[OodaAlert]:
        self._logger.debug(
            "get_terminal_alerts terminal_device_id=%s site_id=%s range=%s-%s cursor=%s",
            terminal_device_id,
            site_id,
            time_range.start,
            time_range.end,
            cursor,
        )
        self._validate_query_params(site_id, time_range, limit)
        params: dict = {
            "terminal_device_id": terminal_device_id,
            "site_id": site_id,
            "start": time_range.start,
            "end": time_range.end,
            "resolution": resolution,
            "limit": limit,
        }
        if cursor:
            params["cursor"] = cursor
        data = self._get_with_retry(
            f"{self._endpoint}/ooda/terminal", params, "get_terminal_alerts", terminal_device_id
        )
        return [OodaAlert.from_dict(a) for a in data.get("alerts", [])]

    def get_site_alerts(
        self,
        site_id: str,
        time_range: TimeRange,
        resolution: str = "5min",
        limit: int = 100,
    ) -> Dict[str, List[OodaAlert]]:
        self._logger.debug(
            "get_site_alerts site_id=%s range=%s-%s", site_id, time_range.start, time_range.end
        )
        self._validate_query_params(site_id, time_range, limit)
        params: dict = {
            "site_id": site_id,
            "start": time_range.start,
            "end": time_range.end,
            "resolution": resolution,
            "limit": limit,
        }
        data = self._get_with_retry(
            f"{self._endpoint}/ooda/site", params, "get_site_alerts", site_id
        )
        result: Dict[str, List[OodaAlert]] = {}
        for tid, alerts in data.get("alerts", {}).items():
            result[tid] = [OodaAlert.from_dict(a) for a in alerts]
        return result

    def get_data_period(
        self,
        site_id: str,
        terminal_device_id: Optional[str] = None,
    ) -> DataPeriod:
        """
        Return the earliest and latest available timestamps for a site or terminal device.
        Call this before get_terminal_alerts to discover what time range has data.
        """
        if not site_id:
            raise ValidationError("site_id is required")
        self._logger.debug(
            "get_data_period site_id=%s terminal_device_id=%s", site_id, terminal_device_id
        )
        params = {"site_id": site_id}
        if terminal_device_id:
            params["terminal_device_id"] = terminal_device_id
        data = self._get_with_retry(
            f"{self._endpoint}/ooda/data-period", params, "get_data_period", site_id
        )
        return DataPeriod(
            site_id=data["site_id"],
            terminal_device_id=data.get("terminal_device_id"),
            first_record=data.get("first_record"),
            last_record=data.get("last_record"),
        )

    def stream_terminal(
        self,
        terminal_device_id: str,
        site_id: str,
        cursor: Optional[str] = None,
        polling_interval: Optional[float] = None,
    ) -> Generator[OodaAlert, None, None]:
        interval = polling_interval if polling_interval is not None else self._polling_interval
        if interval < MIN_POLLING_INTERVAL:
            raise ValidationError(
                f"polling_interval must be >= {MIN_POLLING_INTERVAL}s (got {interval})"
            )
        stream_key = f"terminal:{terminal_device_id}"
        if stream_key in self._active_streams:
            raise ValidationError(
                f"Stream already active for terminal_device_id={terminal_device_id}"
            )
        self._active_streams.add(stream_key)
        last_ts = None
        if cursor:
            cursor_obj = OodaCursorSerializer.deserialize(cursor)
            last_ts = cursor_obj.timestamp
        try:
            while True:
                time_range = TimeRange(
                    start=last_ts if last_ts else "1970-01-01T00:00:00",
                    end="9999-12-31T23:59:59",
                )
                try:
                    alerts = self.get_terminal_alerts(
                        terminal_device_id, site_id, time_range, limit=MAX_LIMIT
                    )
                except ServiceUnavailableError:
                    raise
                for alert in alerts:
                    if last_ts is None or alert.timestamp > last_ts:
                        last_ts = alert.timestamp
                        alert.cursor = OodaCursorSerializer.serialize(terminal_device_id, last_ts)
                        yield alert
                time.sleep(interval)
        finally:
            self._active_streams.discard(stream_key)

    def stream_site(
        self,
        site_id: str,
        cursor: Optional[str] = None,
        polling_interval: Optional[float] = None,
    ) -> Generator[OodaAlert, None, None]:
        interval = polling_interval if polling_interval is not None else self._polling_interval
        if interval < MIN_POLLING_INTERVAL:
            raise ValidationError(
                f"polling_interval must be >= {MIN_POLLING_INTERVAL}s (got {interval})"
            )
        stream_key = f"site:{site_id}"
        if stream_key in self._active_streams:
            raise ValidationError(f"Stream already active for site_id={site_id}")
        self._active_streams.add(stream_key)
        last_ts_per_terminal: Dict[str, str] = {}
        if cursor:
            cursor_obj = OodaCursorSerializer.deserialize(cursor)
            last_ts_per_terminal[cursor_obj.terminal_device_id] = cursor_obj.timestamp
        try:
            while True:
                global_last = (
                    min(last_ts_per_terminal.values())
                    if last_ts_per_terminal
                    else "1970-01-01T00:00:00"
                )
                time_range = TimeRange(start=global_last, end="9999-12-31T23:59:59")
                try:
                    site_data = self.get_site_alerts(site_id, time_range, limit=MAX_LIMIT)
                except ServiceUnavailableError:
                    raise
                new_alerts = []
                for tid, alerts in site_data.items():
                    terminal_last = last_ts_per_terminal.get(tid)
                    for alert in alerts:
                        if terminal_last is None or alert.timestamp > terminal_last:
                            new_alerts.append(alert)
                new_alerts.sort(key=lambda a: a.timestamp)
                for alert in new_alerts:
                    last_ts_per_terminal[alert.terminal_device_id] = alert.timestamp
                    alert.cursor = OodaCursorSerializer.serialize(
                        alert.terminal_device_id, alert.timestamp
                    )
                    yield alert
                time.sleep(interval)
        finally:
            self._active_streams.discard(stream_key)
