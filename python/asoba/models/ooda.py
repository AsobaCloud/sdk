"""OODA alert data models for Ona Platform SDK."""

from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import ValidationError

REQUIRED_FIELDS = [
    "terminal_device_id",
    "site_id",
    "timestamp",
    "alert_type",
    "alert_severity",
    "message",
    "source_system",
    "resolved",
]
OPTIONAL_FIELDS = ["terminal_ts", "metadata"]
STRIP_FIELDS = {"expires_at"}


@dataclass
class OodaAlert:
    terminal_device_id: str
    site_id: str
    timestamp: str
    alert_type: str
    alert_severity: str
    message: str
    source_system: str
    resolved: bool
    terminal_ts: str | None = None
    metadata: dict | None = None
    cursor: str | None = None  # populated by the client, not from DynamoDB

    @classmethod
    def from_dict(cls, data: dict) -> OodaAlert:
        # Strip expires_at
        data = {k: v for k, v in data.items() if k not in STRIP_FIELDS}
        # Validate required fields
        for field in REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                raise ValidationError(f"OodaAlert missing required field: '{field}'")
        # Build kwargs
        kwargs = {f: data[f] for f in REQUIRED_FIELDS}
        for f in OPTIONAL_FIELDS:
            kwargs[f] = data.get(f)
        return cls(**kwargs)


@dataclass
class TimeRange:
    start: str
    end: str


@dataclass
class OodaCursorObject:
    terminal_device_id: str
    timestamp: str


@dataclass
class DataPeriod:
    site_id: str
    terminal_device_id: str | None
    first_record: str | None
    last_record: str | None
