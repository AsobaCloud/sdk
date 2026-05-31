"""ODSE (Ona Data Standardization Engine) model definitions."""

from typing import Set

ODSE_REQUIRED_FIELDS: Set[str] = {"timestamp", "kWh", "error_type"}

ODSE_ALLOWED_FIELDS: Set[str] = {
    "timestamp",
    "kWh",
    "error_type",
    "error_code",
    "kVArh",
    "kVA",
    "PF",
    "asset_id",
    "device_id",
}

ODSE_ERROR_TYPES: Set[str] = {
    "normal",
    "warning",
    "critical",
    "fault",
    "offline",
    "standby",
    "unknown",
}
