"""E2E behavioral tests for ODS-E full-schema validation and conformance profiles.

Exercises the full validation path from entry point to outcome:
- Full 65-field schema acceptance (not just the old 9-field subset)
- Conformance profile validation (all 6 profiles)
- Backward compatibility (existing 9-field records still validate)
- BESS, wind, market settlement, wheeling records validate correctly
"""

import pytest
from ona_platform.utils.validation import validate_odse_record, validate_with_profile, validate_batch
from ona_platform.models.odse import (
    ODSE_ALLOWED_FIELDS,
    ODSE_PROFILES,
    ODSE_ENUM_FIELDS,
    ODSE_NUMERIC_RANGES,
)


class TestFullSchemaAcceptance:
    """B1: Full 65-field schema — records with new fields are accepted, not rejected."""

    def test_bess_record_with_all_new_fields_validates(self):
        """Given a BESS record with soc/soh/charge/discharge/cell fields, When validated,
        Then it passes (no additional_properties_not_allowed)."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
            "direction": "generation",
            "soc": 82.5,
            "soh": 99.1,
            "charge_kWh": 12.0,
            "discharge_kWh": 8.0,
            "cycle_count": 450,
            "cell_temp_min_c": 22.0,
            "cell_temp_max_c": 28.0,
            "cell_voltage_min_v": 3.2,
            "cell_voltage_max_v": 3.65,
            "dispatch_mode": "discharging",
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert is_valid, f"BESS record should validate, got errors: {errors}"
        assert not any("additional_properties" in e for e in errors)

    def test_wind_record_with_all_new_fields_validates(self):
        """Given a wind turbine record with wind_speed/rotor_rpm/blade_pitch/nacelle,
        When validated, Then it passes."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 320.0,
            "error_type": "normal",
            "direction": "generation",
            "wind_speed_ms": 8.5,
            "rotor_rpm": 14.2,
            "blade_pitch_deg": -2.0,
            "nacelle_direction_deg": 270.0,
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert is_valid, f"Wind record should validate, got errors: {errors}"

    def test_market_settlement_record_validates(self):
        """Given a market settlement record with party IDs and settlement periods,
        When validated, Then it passes."""
        record = {
            "timestamp": "2026-06-27T12:00:00+02:00",
            "kWh": 124.6,
            "error_type": "normal",
            "direction": "generation",
            "seller_party_id": "za-nersa:trader:ETANA-001",
            "buyer_party_id": "za-city-capetown:offtaker:SITE-9921",
            "network_operator_id": "za-eskom:network_operator:WC-01",
            "settlement_period_start": "2026-06-27T12:00:00+02:00",
            "settlement_period_end": "2026-06-27T12:30:00+02:00",
            "loss_factor": 0.03,
            "contract_reference": "PPA-001",
            "tariff_schedule_id": "za-city-capetown:cpt:LT-MD-2026:v1",
            "tariff_period": "standard",
            "tariff_currency": "ZAR",
            "energy_charge_component": 358.22,
            "network_charge_component": 62.91,
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert is_valid, f"Market record should validate, got errors: {errors}"

    def test_wheeling_record_with_all_fields_validates(self):
        """Given a wheeling record with injection/offtake points and wheeling status,
        When validated, Then it passes."""
        record = {
            "timestamp": "2026-06-27T14:00:00+02:00",
            "kWh": 87.3,
            "error_type": "normal",
            "direction": "generation",
            "wheeling_type": "virtual",
            "injection_point_id": "NCAPE-SOLAR-GEN-12",
            "offtake_point_id": "CCT-DIST-MV-BELLVILLE-03",
            "wheeling_status": "confirmed",
            "wheeling_path_id": "PATH-001",
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert is_valid, f"Wheeling record should validate, got errors: {errors}"


class TestConformanceProfiles:
    """B2: All 6 conformance profiles work correctly."""

    def test_bilateral_profile_passes_with_all_required(self):
        """Given a valid bilateral trade record, When validated with bilateral profile,
        Then it passes."""
        record = {
            "timestamp": "2026-06-27T14:00:00+02:00",
            "kWh": 87.3,
            "error_type": "normal",
            "seller_party_id": "nersa:gen:SOLARPK-001",
            "buyer_party_id": "nersa:offtaker:MUN042",
            "settlement_period_start": "2026-06-27T14:00:00+02:00",
            "settlement_period_end": "2026-06-27T14:30:00+02:00",
            "contract_reference": "PPA-SOLARPK-MUN042-2025-003",
            "settlement_type": "bilateral",
        }
        is_valid, errors, _ = validate_with_profile(record, "bilateral")
        assert is_valid, f"Bilateral profile should pass, got errors: {errors}"

    def test_bilateral_profile_fails_missing_settlement_type(self):
        """Given a bilateral record missing settlement_type, When validated with
        bilateral profile, Then it fails with profile_field_missing."""
        record = {
            "timestamp": "2026-06-27T14:00:00+02:00",
            "kWh": 87.3,
            "error_type": "normal",
            "seller_party_id": "nersa:gen:SOLARPK-001",
            "buyer_party_id": "nersa:offtaker:MUN042",
            "settlement_period_start": "2026-06-27T14:00:00+02:00",
            "settlement_period_end": "2026-06-27T14:30:00+02:00",
            "contract_reference": "PPA-001",
        }
        is_valid, errors, _ = validate_with_profile(record, "bilateral")
        assert not is_valid
        assert any("profile_field_missing:settlement_type" in e for e in errors)

    def test_bilateral_profile_fails_wrong_settlement_type(self):
        """Given a record with settlement_type=sawem_day_ahead, When validated with
        bilateral profile, Then it fails with profile_value_mismatch."""
        record = {
            "timestamp": "2026-06-27T14:00:00+02:00",
            "kWh": 87.3,
            "error_type": "normal",
            "seller_party_id": "nersa:gen:SOLARPK-001",
            "buyer_party_id": "nersa:offtaker:MUN042",
            "settlement_period_start": "2026-06-27T14:00:00+02:00",
            "settlement_period_end": "2026-06-27T14:30:00+02:00",
            "contract_reference": "PPA-001",
            "settlement_type": "sawem_day_ahead",
        }
        is_valid, errors, _ = validate_with_profile(record, "bilateral")
        assert not is_valid
        assert any("profile_value_mismatch:settlement_type" in e for e in errors)

    def test_wheeling_profile_passes_with_all_required(self):
        """Given a valid wheeling record, When validated with wheeling profile,
        Then it passes."""
        record = {
            "timestamp": "2026-06-27T14:00:00+02:00",
            "kWh": 87.3,
            "error_type": "normal",
            "seller_party_id": "nersa:trader:ENPOWER-001",
            "buyer_party_id": "za-city-capetown:offtaker:METRO-4401",
            "settlement_period_start": "2026-06-27T14:00:00+02:00",
            "settlement_period_end": "2026-06-27T14:30:00+02:00",
            "contract_reference": "PPA-ENPOWER-CCT-2025-017",
            "settlement_type": "bilateral",
            "network_operator_id": "nersa:dso:eskom-tx",
            "wheeling_type": "virtual",
            "injection_point_id": "NCAPE-SOLAR-GEN-12",
            "offtake_point_id": "CCT-DIST-MV-BELLVILLE-03",
            "wheeling_status": "confirmed",
            "loss_factor": 0.032,
        }
        is_valid, errors, _ = validate_with_profile(record, "wheeling")
        assert is_valid, f"Wheeling profile should pass, got errors: {errors}"

    def test_sawem_brp_profile_passes(self):
        """Given a valid SAWEM BRP record, When validated with sawem_brp profile,
        Then it passes."""
        record = {
            "timestamp": "2026-06-27T15:00:00+02:00",
            "kWh": 312.5,
            "error_type": "normal",
            "seller_party_id": "nersa:gen:WINDCO-007",
            "balance_responsible_party_id": "nersa:brp:BRP-01",
            "settlement_type": "sawem_day_ahead",
            "forecast_kWh": 320.0,
            "settlement_period_start": "2026-06-27T15:00:00+02:00",
            "settlement_period_end": "2026-06-27T15:30:00+02:00",
            "imbalance_kWh": -7.5,
        }
        is_valid, errors, _ = validate_with_profile(record, "sawem_brp")
        assert is_valid, f"SAWEM BRP profile should pass, got errors: {errors}"

    def test_municipal_recon_profile_passes(self):
        """Given a valid municipal reconciliation record, When validated with
        municipal_recon profile, Then it passes."""
        record = {
            "timestamp": "2026-06-27T10:00:00+02:00",
            "kWh": 45.2,
            "error_type": "normal",
            "direction": "consumption",
            "buyer_party_id": "za-city-emfuleni:municipality:EMF",
            "billing_period": "2026-06",
            "billed_kWh": 44.8,
            "billing_status": "adjusted",
            "daa_reference": "DAA-ESKOM-EMFULENI-2025-001",
        }
        is_valid, errors, _ = validate_with_profile(record, "municipal_recon")
        assert is_valid, f"Municipal recon profile should pass, got errors: {errors}"

    def test_bess_dispatch_profile_passes(self):
        """Given a valid BESS dispatch record, When validated with bess_dispatch
        profile, Then it passes."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
            "dispatch_mode": "charging",
            "soc": 75.0,
        }
        is_valid, errors, _ = validate_with_profile(record, "bess_dispatch")
        assert is_valid, f"BESS dispatch profile should pass, got errors: {errors}"

    def test_bess_dispatch_profile_fails_missing_soc(self):
        """Given a BESS record missing soc, When validated with bess_dispatch profile,
        Then it fails with profile_field_missing:soc."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
            "dispatch_mode": "charging",
        }
        is_valid, errors, _ = validate_with_profile(record, "bess_dispatch")
        assert not is_valid
        assert any("profile_field_missing:soc" in e for e in errors)

    def test_wind_scada_profile_passes(self):
        """Given a valid wind SCADA record, When validated with wind_scada profile,
        Then it passes."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 320.0,
            "error_type": "normal",
            "wind_speed_ms": 8.5,
        }
        is_valid, errors, _ = validate_with_profile(record, "wind_scada")
        assert is_valid, f"Wind SCADA profile should pass, got errors: {errors}"

    def test_wind_scada_profile_fails_missing_wind_speed(self):
        """Given a record without wind_speed_ms, When validated with wind_scada profile,
        Then it fails with profile_field_missing:wind_speed_ms."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 320.0,
            "error_type": "normal",
        }
        is_valid, errors, _ = validate_with_profile(record, "wind_scada")
        assert not is_valid
        assert any("profile_field_missing:wind_speed_ms" in e for e in errors)

    def test_unknown_profile_returns_error(self):
        """Given a valid record, When validated with an unknown profile name,
        Then it fails with unknown_profile error."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
        }
        is_valid, errors, _ = validate_with_profile(record, "nonexistent_profile")
        assert not is_valid
        assert any("unknown_profile" in e for e in errors)


class TestBackwardCompatibility:
    """B3: Existing 9-field records still validate without errors."""

    def test_minimal_3_field_record_validates(self):
        """Given a minimal record with only required fields, When validated,
        Then it passes."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 100.0,
            "error_type": "normal",
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert is_valid, f"Minimal record should validate, got errors: {errors}"

    def test_old_9_field_record_validates(self):
        """Given a record with the old 9-field subset, When validated,
        Then it passes without additional_properties errors."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 100.0,
            "error_type": "normal",
            "error_code": "E001",
            "kVArh": 5.0,
            "kVA": 120.0,
            "PF": 0.95,
            "asset_id": "INV001",
            "device_id": "DEV001",
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert is_valid, f"Old 9-field record should validate, got errors: {errors}"

    def test_batch_validation_still_works(self):
        """Given a batch of mixed valid/invalid records, When validated with
        validate_batch, Then the split is correct."""
        records = [
            {"timestamp": "2026-06-27T10:00:00Z", "kWh": 100.0, "error_type": "normal"},
            {"timestamp": "invalid", "kWh": "not-a-number", "error_type": "unknown"},
        ]
        result = validate_batch(records)
        assert result["summary"]["total"] == 2
        assert result["summary"]["valid"] == 1
        assert result["summary"]["invalid"] == 1


class TestEnumAndRangeValidation:
    """B4: New enum and range constraints are enforced for the full field set."""

    def test_invalid_dispatch_mode_rejected(self):
        """Given a record with dispatch_mode='exploding', When validated,
        Then it fails with dispatch_mode_enum_mismatch."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
            "dispatch_mode": "exploding",
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert not is_valid
        assert any("dispatch_mode_enum_mismatch" in e for e in errors)

    def test_soc_out_of_range_rejected(self):
        """Given a record with soc=150, When validated, Then it fails with
        soc_out_of_bounds."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
            "soc": 150.0,
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert not is_valid
        assert any("soc_out_of_bounds" in e for e in errors)

    def test_nacelle_direction_out_of_range_rejected(self):
        """Given a record with nacelle_direction_deg=400, When validated,
        Then it fails with nacelle_direction_deg_out_of_bounds."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
            "nacelle_direction_deg": 400.0,
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert not is_valid
        assert any("nacelle_direction_deg_out_of_bounds" in e for e in errors)

    def test_invalid_settlement_type_rejected(self):
        """Given a record with settlement_type='bogus', When validated,
        Then it fails with settlement_type_enum_mismatch."""
        record = {
            "timestamp": "2026-06-27T10:00:00Z",
            "kWh": 50.0,
            "error_type": "normal",
            "settlement_type": "bogus",
        }
        is_valid, errors, _ = validate_odse_record(record)
        assert not is_valid
        assert any("settlement_type_enum_mismatch" in e for e in errors)


class TestSchemaCompleteness:
    """B5: The SDK's field set matches the ODS-E energy-timeseries schema."""

    def test_allowed_fields_count_matches_schema(self):
        """Given the ODSE_ALLOWED_FIELDS set, When counted, Then it has 67 fields
        (65 from energy-timeseries.json + 2 SDK backward-compat extensions)."""
        assert len(ODSE_ALLOWED_FIELDS) == 67, (
            f"Expected 67 fields (65 schema + 2 backward-compat), got {len(ODSE_ALLOWED_FIELDS)}"
        )

    def test_all_6_profiles_defined(self):
        """Given the ODSE_PROFILES dict, When keys are checked, Then all 6
        conformance profiles are present."""
        expected = {"bilateral", "wheeling", "sawem_brp", "municipal_recon", "bess_dispatch", "wind_scada"}
        assert set(ODSE_PROFILES.keys()) == expected

    def test_enum_fields_cover_all_constrained_strings(self):
        """Given the ODSE_ENUM_FIELDS dict, When checked, Then it covers all
        enum-constrained fields from the schema."""
        expected_enum_fields = {
            "error_type", "direction", "end_use", "fuel_type",
            "tariff_period", "dispatch_mode", "wheeling_type",
            "wheeling_status", "settlement_type", "billing_status",
            "certificate_standard", "verification_status", "curtailment_type",
        }
        assert set(ODSE_ENUM_FIELDS.keys()) == expected_enum_fields
