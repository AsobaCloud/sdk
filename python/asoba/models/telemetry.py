"""Telemetry data models for Ona Platform SDK."""

from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import ValidationError

REQUIRED_FIELDS = [
    "asset_id",
    "site_id",
    "timestamp",
    "power",
    "kWh",
    "inverter_state",
    "run_state",
]
OPTIONAL_FIELDS = ["asset_ts", "kVArh", "kVA", "PF", "temperature", "soc", "soh", "error_code", "error_type"]
STRIP_FIELDS = {"expires_at"}


@dataclass
class TelemetryRecord:
    asset_id: str
    site_id: str
    timestamp: str
    power: float
    kWh: float
    inverter_state: int
    run_state: int
    asset_ts: str | None = None
    kVArh: float | None = None
    kVA: float | None = None
    PF: float | None = None
    temperature: float | None = None
    soc: float | None = None
    soh: float | None = None
    error_code: str | None = None
    error_type: str | None = None
    cursor: str | None = None  # populated by the client, not from DynamoDB

    @classmethod
    def from_dict(cls, data: dict) -> TelemetryRecord:
        # Strip expires_at
        data = {k: v for k, v in data.items() if k not in STRIP_FIELDS}
        # Validate required fields
        for field in REQUIRED_FIELDS:
            if field not in data or data[field] is None:
                raise ValidationError(f"TelemetryRecord missing required field: '{field}'")
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
class CursorObject:
    asset_id: str
    timestamp: str
