"""Property-based tests for TelemetryRecord model."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ona_platform.models.telemetry import TelemetryRecord, REQUIRED_FIELDS, OPTIONAL_FIELDS
from ona_platform.exceptions import ValidationError

# Strategies for required field values
_required_strategy = st.fixed_dictionaries(
    {
        "asset_id": st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
            ),
        ),
        "site_id": st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_"
            ),
        ),
        "timestamp": st.just("2025-01-01T00:00:00"),
        "asset_ts": st.just("INV-001#2025-01-01T00:00:00"),
        "power": st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
        "kWh": st.floats(min_value=0.0, max_value=1000000.0, allow_nan=False, allow_infinity=False),
        "inverter_state": st.integers(min_value=0, max_value=255),
        "run_state": st.integers(min_value=0, max_value=255),
    }
)


# Feature: inverter-telemetry-streaming, Property 9: TelemetryRecord contains all required fields with correct types; expires_at absent
@given(_required_strategy)
@settings(max_examples=100)
def test_property_9_required_fields_present_and_expires_at_absent(base_data):
    """Validates: Requirements 6.1, 6.2, 6.3"""
    data = dict(base_data)
    data["expires_at"] = "2099-01-01T00:00:00"  # should be stripped

    record = TelemetryRecord.from_dict(data)

    assert record.asset_id == data["asset_id"]
    assert record.site_id == data["site_id"]
    assert record.timestamp == data["timestamp"]
    assert record.asset_ts == data["asset_ts"]
    assert isinstance(record.power, float)
    assert isinstance(record.kWh, float)
    assert isinstance(record.inverter_state, int)
    assert isinstance(record.run_state, int)
    assert not hasattr(record, "expires_at")


# Feature: inverter-telemetry-streaming, Property 10: Missing required field raises ValidationError with field name
@given(_required_strategy, st.sampled_from(REQUIRED_FIELDS))
@settings(max_examples=100)
def test_property_10_missing_required_field_raises_validation_error(base_data, missing_field):
    """Validates: Requirements 6.4"""
    data = dict(base_data)
    del data[missing_field]

    with pytest.raises(ValidationError) as exc_info:
        TelemetryRecord.from_dict(data)

    assert missing_field in str(exc_info.value)


# Feature: inverter-telemetry-streaming, Property 11: Absent optional fields default to None without error
@given(_required_strategy)
@settings(max_examples=100)
def test_property_11_absent_optional_fields_default_to_none(base_data):
    """Validates: Requirements 6.5"""
    data = dict(base_data)
    # Ensure no optional fields are present
    for f in OPTIONAL_FIELDS:
        data.pop(f, None)

    record = TelemetryRecord.from_dict(data)

    assert record.kVArh is None
    assert record.kVA is None
    assert record.PF is None
    assert record.temperature is None
    assert record.error_code is None
    assert record.error_type is None
