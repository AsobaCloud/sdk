import pytest
from ona_platform.utils.validation import validate_odse_record, validate_batch


def test_validate_odse_record_accepts_valid_minimal_record():
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": 12.5,
        "error_type": "normal",
    }

    is_valid, errors, normalized = validate_odse_record(record)

    assert is_valid is True
    assert errors == []
    assert normalized["kWh"] == 12.5
    assert normalized["timestamp"] == "2026-02-11T12:00:00Z"


def test_validate_odse_record_accepts_valid_minimal_record_naive_string():
    # Service uses pd.to_datetime(..., utc=True) which handles naive strings as UTC
    # Our SDK implementation adds UTC if missing to match this behavior
    record = {
        "timestamp": "2026-02-11 12:00:00",
        "kWh": 12.5,
        "error_type": "normal",
    }

    is_valid, errors, normalized = validate_odse_record(record)

    assert is_valid is True
    assert normalized["timestamp"] == "2026-02-11T12:00:00Z"


def test_validate_odse_record_rejects_missing_required():
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": 5.0,
    }

    is_valid, errors, _ = validate_odse_record(record)

    assert is_valid is False
    assert any("missing_required_fields" in err for err in errors)
    assert "error_type" in errors[0]


def test_validate_odse_record_rejects_invalid_error_type():
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": 5.0,
        "error_type": "bad_status",
    }

    is_valid, errors, _ = validate_odse_record(record)

    assert is_valid is False
    assert "error_type_enum_mismatch" in errors


def test_validate_odse_record_rejects_negative_kwh():
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": -1.0,
        "error_type": "normal",
    }

    is_valid, errors, _ = validate_odse_record(record)

    assert is_valid is False
    assert "kwh_out_of_bounds" in errors


def test_validate_odse_record_rejects_additional_properties():
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": 2.0,
        "error_type": "normal",
        "power_kw": 10.0,
    }

    is_valid, errors, _ = validate_odse_record(record)

    assert is_valid is False
    assert any("additional_properties_not_allowed" in err for err in errors)
    assert "power_kw" in errors[0]


def test_validate_batch_counts_rows():
    records = [
        {"timestamp": "2026-02-11T12:00:00Z", "kWh": 1.0, "error_type": "normal"},
        {"timestamp": "2026-02-11T12:05:00Z", "kWh": -1.0, "error_type": "normal"},
    ]

    result = validate_batch(records)

    assert result["summary"]["total"] == 2
    assert result["summary"]["valid"] == 1
    assert result["summary"]["invalid"] == 1
    assert result["invalid_records"][0]["index"] == 1
    assert "kwh_out_of_bounds" in result["invalid_records"][0]["errors"]


def test_clean_record_strips_whitespace():
    record = {
        "timestamp": " 2026-02-11T12:00:00Z ",
        "kWh": 12.5,
        "error_type": " normal ",
    }

    is_valid, errors, normalized = validate_odse_record(record)

    assert is_valid is True
    assert normalized["timestamp"] == "2026-02-11T12:00:00Z"
    assert normalized["error_type"] == "normal"


def test_clean_record_handles_nan():
    # Using float('nan') to simulate math.nan/pd.NA
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": float('nan'),
        "error_type": "normal",
    }

    is_valid, errors, _ = validate_odse_record(record)

    assert is_valid is False
    assert any("missing_required_fields:kWh" in err for err in errors)


def test_validate_odse_record_optional_numeric_fields():
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": 10.0,
        "error_type": "normal",
        "kVArh": 2.5,
        "kVA": 10.5,
        "PF": 0.95
    }

    is_valid, errors, normalized = validate_odse_record(record)

    assert is_valid is True
    assert normalized["kVArh"] == 2.5
    assert normalized["kVA"] == 10.5
    assert normalized["PF"] == 0.95


def test_validate_odse_record_rejects_out_of_bounds_optional():
    record = {
        "timestamp": "2026-02-11T12:00:00Z",
        "kWh": 10.0,
        "error_type": "normal",
        "PF": 1.2
    }

    is_valid, errors, _ = validate_odse_record(record)

    assert is_valid is False
    assert "pf_out_of_bounds" in errors
