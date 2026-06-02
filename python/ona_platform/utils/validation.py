"""Validation utilities for ODSE records."""

import math
from typing import Dict, Any, List, Tuple, Optional

from dateutil.parser import parse as parse_date

from ..models.odse import (
    ODSE_REQUIRED_FIELDS,
    ODSE_ALLOWED_FIELDS,
    ODSE_ERROR_TYPES,
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
    """Validate a single record against ODSE production-timeseries constraints.
    
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
            # dateutil.parser is more flexible and matches pandas behavior better than fromisoformat
            ts = parse_date(str(timestamp_raw))
            # Ensure UTC/Z suffix consistency
            if ts.tzinfo is None:
                # If no timezone, assume UTC to match service behavior for naive strings if any
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

    # Validate error_type
    error_type = cleaned.get("error_type")
    if error_type is not None and error_type not in ODSE_ERROR_TYPES:
        errors.append("error_type_enum_mismatch")

    # Validate optional numeric fields
    kvarh = _to_float(cleaned.get("kVArh"))
    if cleaned.get("kVArh") is not None and kvarh is None:
        errors.append("kvarh_not_numeric")
    elif kvarh is not None:
        normalized["kVArh"] = kvarh

    kva = _to_float(cleaned.get("kVA"))
    if cleaned.get("kVA") is not None and kva is None:
        errors.append("kva_not_numeric")
    elif kva is not None:
        if kva < 0:
            errors.append("kva_out_of_bounds")
        normalized["kVA"] = kva

    pf = _to_float(cleaned.get("PF"))
    if cleaned.get("PF") is not None and pf is None:
        errors.append("pf_not_numeric")
    elif pf is not None:
        if pf < 0 or pf > 1:
            errors.append("pf_out_of_bounds")
        normalized["PF"] = pf

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
