"""Validation utilities for ODS-E (Open Data Schema for Energy) records.

Supports the full energy-timeseries v1 schema (65 fields) and 6 conformance
profiles (bilateral, wheeling, sawem_brp, municipal_recon, bess_dispatch,
wind_scada).

Backward-compatible: existing 9-field callers of ``validate_odse_record``
and ``validate_batch`` are unaffected.
"""

import math
from typing import Dict, Any, List, Tuple, Optional

from dateutil.parser import parse as parse_date

from ..models.odse import (
    ODSE_REQUIRED_FIELDS,
    ODSE_ALLOWED_FIELDS,
    ODSE_ERROR_TYPES,
    ODSE_ENUM_FIELDS,
    ODSE_NUMERIC_RANGES,
    ODSE_PROFILES,
)


def _is_nan(value: Any) -> bool:
    """Check if a value is NaN (float or int)."""
    if isinstance(value, (float, int)):
        return math.isnan(value)
    return False


def clean_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Clean a single record by stripping whitespace and handling nulls.

    Equivalent to service-side cleaning but without pandas dependency.
    """
    cleaned = {}
    for key, value in record.items():
        if value is None or _is_nan(value):
            cleaned[key] = None
            continue
        if isinstance(value, str):
            stripped = value.strip()
            cleaned[key] = stripped if stripped != "" else None
            continue
        cleaned[key] = value
    return cleaned


def _to_float(value: Any) -> Optional[float]:
    """Convert value to float, handling None and NaN."""
    if value is None or _is_nan(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate_odse_record(record: Dict[str, Any]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate a single record against ODS-E energy-timeseries constraints.

    Checks required fields, allowed fields, timestamp format, numeric ranges,
    and enum values for the full 65-field schema.

    Returns:
        (is_valid, list_of_errors, normalized_record)
    """
    errors = []
    cleaned = clean_record(record)

    # Check for missing required fields
    missing = [f for f in ODSE_REQUIRED_FIELDS if cleaned.get(f) is None]
    if missing:
        errors.append(f"missing_required_fields:{','.join(sorted(missing))}")

    # Check for additional fields not allowed
    extra_fields = sorted(set(cleaned.keys()) - ODSE_ALLOWED_FIELDS)
    if extra_fields:
        errors.append(f"additional_properties_not_allowed:{','.join(extra_fields)}")

    normalized = dict(cleaned)

    # Validate timestamp
    timestamp_raw = cleaned.get("timestamp")
    if timestamp_raw is not None:
        try:
            ts = parse_date(str(timestamp_raw))
            if ts.tzinfo is None:
                from datetime import timezone
                ts = ts.replace(tzinfo=timezone.utc)
            normalized["timestamp"] = ts.isoformat().replace("+00:00", "Z")
        except (ValueError, OverflowError, TypeError):
            errors.append("invalid_timestamp")

    # Validate kWh
    kwh_value = _to_float(cleaned.get("kWh"))
    if cleaned.get("kWh") is not None and kwh_value is None:
        errors.append("kwh_not_numeric")
    elif kwh_value is not None:
        if kwh_value < 0:
            errors.append("kwh_out_of_bounds")
        normalized["kWh"] = kwh_value

    # Validate enum fields (error_type + all other enum-constrained strings)
    for field_name, allowed_values in ODSE_ENUM_FIELDS.items():
        value = cleaned.get(field_name)
        if value is not None and value not in allowed_values:
            errors.append(f"{field_name.lower()}_enum_mismatch")

    # Validate numeric fields with range constraints
    for field_name, (min_val, max_val) in ODSE_NUMERIC_RANGES.items():
        raw = cleaned.get(field_name)
        if raw is None:
            continue
        num = _to_float(raw)
        if num is None:
            errors.append(f"{field_name.lower()}_not_numeric")
            continue
        if min_val is not None and num < min_val:
            errors.append(f"{field_name.lower()}_out_of_bounds")
            continue
        if max_val is not None and num > max_val:
            errors.append(f"{field_name.lower()}_out_of_bounds")
            continue
        normalized[field_name] = num

    # Validate kVArh (numeric, no range constraint but keep original behavior)
    kvarh = _to_float(cleaned.get("kVArh"))
    if cleaned.get("kVArh") is not None and kvarh is None:
        errors.append("kvarh_not_numeric")
    elif kvarh is not None:
        normalized["kVArh"] = kvarh

    return len(errors) == 0, errors, normalized


def validate_with_profile(
    record: Dict[str, Any], profile: str
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Validate a record against an ODS-E conformance profile.

    Profile validation runs **after** schema validation passes. If schema
    validation produces errors, those are returned and profile checks are
    skipped (prevents duplicate/confusing errors).

    Profiles (SEP-002 + SEP-025 + SEP-026):
        - ``bilateral`` — PPA / bilateral trade settlement
        - ``wheeling`` — wheeled energy across networks
        - ``sawem_brp`` — wholesale market (SAWEM) settlement for BRPs
        - ``municipal_recon`` — municipal billing / reconciliation
        - ``bess_dispatch`` — BESS dispatch validation (SEP-026)
        - ``wind_scada`` — wind turbine SCADA validation (SEP-025)

    Returns:
        (is_valid, list_of_errors, normalized_record)

    Error codes:
        - ``unknown_profile`` — profile name not recognised
        - ``profile_field_missing:<field>`` — required field absent
        - ``profile_value_mismatch:<field>`` — value not in allowed set
    """
    # Step 1: schema validation
    is_valid, errors, normalized = validate_odse_record(record)
    if not is_valid:
        return is_valid, errors, normalized

    # Step 2: profile validation
    if profile not in ODSE_PROFILES:
        errors.append(f"unknown_profile:{profile}")
        return False, errors, normalized

    spec = ODSE_PROFILES[profile]

    # Check required fields are present
    for field_name in spec["required"]:
        if normalized.get(field_name) is None:
            errors.append(f"profile_field_missing:{field_name}")

    # Check value constraints
    for field_name, allowed_values in spec.get("value_constraints", {}).items():
        value = normalized.get(field_name)
        if value is not None and value not in allowed_values:
            errors.append(f"profile_value_mismatch:{field_name}")

    return len(errors) == 0, errors, normalized


def validate_batch(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate a batch of records and return valid/invalid split.

    Returns:
        {
            "valid_records": List[dict],
            "invalid_records": List[dict],
            "summary": {
                "total": int,
                "valid": int,
                "invalid": int
            }
        }
    """
    valid_records = []
    invalid_records = []

    for idx, record in enumerate(records):
        is_valid, errors, normalized = validate_odse_record(record)
        if is_valid:
            valid_records.append(normalized)
        else:
            invalid_records.append({
                "index": idx,
                "errors": errors,
                "record": record
            })

    return {
        "valid_records": valid_records,
        "invalid_records": invalid_records,
        "summary": {
            "total": len(records),
            "valid": len(valid_records),
            "invalid": len(invalid_records)
        }
    }
