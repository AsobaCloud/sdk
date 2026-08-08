"""ODS-E (Open Data Schema for Energy) model definitions.

Reflects the full energy-timeseries schema (v1) from the ona-protocol spec:
https://github.com/AsobaCloud/ona-protocol/blob/main/schemas/energy-timeseries.json

All fields except timestamp, kWh, and error_type are optional and additive.
Existing 9-field callers remain valid without modification.
"""

from typing import Dict, Set

# ---------------------------------------------------------------------------
# Required fields (per energy-timeseries.json "required")
# ---------------------------------------------------------------------------
ODSE_REQUIRED_FIELDS: Set[str] = {"timestamp", "kWh", "error_type"}

# ---------------------------------------------------------------------------
# Full allowed field set (65 properties from energy-timeseries.json)
# ---------------------------------------------------------------------------
ODSE_ALLOWED_FIELDS: Set[str] = {
    # Core telemetry
    "timestamp",
    "kWh",
    "error_type",
    "error_code",
    "kVArh",
    "kVA",
    "PF",
    "direction",
    # End-use & fuel
    "end_use",
    "fuel_type",
    # Market settlement
    "seller_party_id",
    "buyer_party_id",
    "network_operator_id",
    "wheeling_agent_id",
    "settlement_period_start",
    "settlement_period_end",
    "loss_factor",
    "contract_reference",
    # Tariff
    "tariff_schedule_id",
    "tariff_period",
    "tariff_currency",
    "tariff_version_effective_at",
    "energy_charge_component",
    "network_charge_component",
    # Wheeling
    "wheeling_type",
    "injection_point_id",
    "offtake_point_id",
    "wheeling_status",
    "wheeling_path_id",
    # Unbundled charges
    "generation_charge_component",
    "transmission_charge_component",
    "distribution_charge_component",
    "ancillary_service_charge_component",
    "non_bypassable_charge_component",
    "environmental_levy_component",
    # Curtailment
    "curtailment_flag",
    "curtailment_type",
    "curtailed_kWh",
    "curtailment_instruction_id",
    # Balance responsibility
    "balance_responsible_party_id",
    "forecast_kWh",
    "imbalance_kWh",
    "settlement_type",
    # Billing
    "billing_period",
    "billed_kWh",
    "billing_status",
    "daa_reference",
    # Renewable certificates
    "renewable_attribute_id",
    "certificate_standard",
    "verification_status",
    # Carbon
    "carbon_intensity_gCO2_per_kWh",
    # BESS (SEP-026)
    "soc",
    "soh",
    "charge_kWh",
    "discharge_kWh",
    "cycle_count",
    "cell_temp_min_c",
    "cell_temp_max_c",
    "cell_voltage_min_v",
    "cell_voltage_max_v",
    "dispatch_mode",
    # Wind (SEP-025)
    "wind_speed_ms",
    "rotor_rpm",
    "blade_pitch_deg",
    "nacelle_direction_deg",
    # SDK backward-compat extensions (not in energy-timeseries.json but
    # accepted by prior SDK versions to avoid breaking existing callers)
    "asset_id",
    "device_id",
}

# ---------------------------------------------------------------------------
# Enum sets for string fields with constrained values
# ---------------------------------------------------------------------------
ODSE_ERROR_TYPES: Set[str] = {
    "normal",
    "warning",
    "critical",
    "fault",
    "offline",
    "standby",
    "unknown",
}

ODSE_DIRECTIONS: Set[str] = {
    "generation",
    "consumption",
    "net",
}

ODSE_END_USES: Set[str] = {
    "cooling", "heating", "fans", "pumps", "water_systems",
    "interior_lighting", "exterior_lighting", "interior_equipment",
    "refrigeration", "cooking", "laundry", "ev_charging",
    "pv_generation", "battery_storage", "whole_building", "other",
}

ODSE_FUEL_TYPES: Set[str] = {
    "electricity", "natural_gas", "propane", "fuel_oil", "other",
}

ODSE_TARIFF_PERIODS: Set[str] = {
    "peak", "standard", "off_peak", "critical_peak",
}

ODSE_DISPATCH_MODES: Set[str] = {
    "charging", "discharging", "standby", "balancing",
}

ODSE_WHEELING_TYPES: Set[str] = {
    "traditional", "virtual", "portfolio",
}

ODSE_WHEELING_STATUSES: Set[str] = {
    "provisional", "confirmed", "reconciled", "disputed",
}

ODSE_SETTLEMENT_TYPES: Set[str] = {
    "bilateral", "sawem_day_ahead", "sawem_intra_day", "balancing", "ancillary",
}

ODSE_BILLING_STATUSES: Set[str] = {
    "metered", "estimated", "adjusted", "disputed",
}

ODSE_CERTIFICATE_STANDARDS: Set[str] = {
    "i_rec", "rego", "go", "rec", "tigr", "other",
}

ODSE_VERIFICATION_STATUSES: Set[str] = {
    "pending", "issued", "retired", "cancelled",
}

ODSE_CURTAILMENT_TYPES: Set[str] = {
    "congestion", "frequency", "voltage", "instruction", "other",
}

ODSE_ASSET_TYPES: Set[str] = {
    "solar_pv", "wind_turbine", "battery_storage", "grid_meter",
    "ev_charger", "hvac_system", "generator", "chp", "fuel_cell", "other",
}

# ---------------------------------------------------------------------------
# Conformance profiles (SEP-002 + SEP-025 + SEP-026)
# ---------------------------------------------------------------------------
# Each profile maps to:
#   "required": list of field names that must be present
#   "value_constraints": dict of field -> set of allowed values

ODSE_PROFILES: Dict[str, Dict] = {
    # --- SEP-002: SA Trading Conformance Profiles ---
    "bilateral": {
        "required": [
            "seller_party_id",
            "buyer_party_id",
            "settlement_period_start",
            "settlement_period_end",
            "contract_reference",
            "settlement_type",
        ],
        "value_constraints": {
            "settlement_type": {"bilateral"},
        },
    },
    "wheeling": {
        "required": [
            "seller_party_id",
            "buyer_party_id",
            "settlement_period_start",
            "settlement_period_end",
            "contract_reference",
            "settlement_type",
            "network_operator_id",
            "wheeling_type",
            "injection_point_id",
            "offtake_point_id",
            "wheeling_status",
            "loss_factor",
        ],
        "value_constraints": {
            "settlement_type": {"bilateral"},
        },
    },
    "sawem_brp": {
        "required": [
            "seller_party_id",
            "balance_responsible_party_id",
            "settlement_type",
            "forecast_kWh",
            "settlement_period_start",
            "settlement_period_end",
        ],
        "value_constraints": {
            "settlement_type": {
                "sawem_day_ahead",
                "sawem_intra_day",
                "balancing",
                "ancillary",
            },
        },
    },
    "municipal_recon": {
        "required": [
            "buyer_party_id",
            "billing_period",
            "billed_kWh",
            "billing_status",
        ],
        "value_constraints": {},
    },
    # --- SEP-026: BESS Dispatch ---
    "bess_dispatch": {
        "required": [
            "dispatch_mode",
            "soc",
        ],
        "value_constraints": {
            "dispatch_mode": ODSE_DISPATCH_MODES,
        },
    },
    # --- SEP-025: Wind SCADA ---
    "wind_scada": {
        "required": [
            "wind_speed_ms",
        ],
        "value_constraints": {},
    },
}

# ---------------------------------------------------------------------------
# Numeric field range constraints: field -> (min, max) or (min, None)
# ---------------------------------------------------------------------------
ODSE_NUMERIC_RANGES: Dict[str, tuple] = {
    "kVA": (0, None),
    "PF": (0, 1),
    "soc": (0, 100),
    "soh": (0, 100),
    "charge_kWh": (0, None),
    "discharge_kWh": (0, None),
    "cycle_count": (0, None),
    "cell_voltage_min_v": (0, None),
    "cell_voltage_max_v": (0, None),
    "wind_speed_ms": (0, None),
    "rotor_rpm": (0, None),
    "nacelle_direction_deg": (0, 360),
    "loss_factor": (0, None),
    "energy_charge_component": (0, None),
    "network_charge_component": (0, None),
    "generation_charge_component": (0, None),
    "transmission_charge_component": (0, None),
    "distribution_charge_component": (0, None),
    "ancillary_service_charge_component": (0, None),
    "non_bypassable_charge_component": (0, None),
    "environmental_levy_component": (0, None),
    "curtailed_kWh": (0, None),
    "billed_kWh": (0, None),
    "carbon_intensity_gCO2_per_kWh": (0, None),
}

# ---------------------------------------------------------------------------
# Enum field mapping: field -> allowed values set
# ---------------------------------------------------------------------------
ODSE_ENUM_FIELDS: Dict[str, Set[str]] = {
    "error_type": ODSE_ERROR_TYPES,
    "direction": ODSE_DIRECTIONS,
    "end_use": ODSE_END_USES,
    "fuel_type": ODSE_FUEL_TYPES,
    "tariff_period": ODSE_TARIFF_PERIODS,
    "dispatch_mode": ODSE_DISPATCH_MODES,
    "wheeling_type": ODSE_WHEELING_TYPES,
    "wheeling_status": ODSE_WHEELING_STATUSES,
    "settlement_type": ODSE_SETTLEMENT_TYPES,
    "billing_status": ODSE_BILLING_STATUSES,
    "certificate_standard": ODSE_CERTIFICATE_STANDARDS,
    "verification_status": ODSE_VERIFICATION_STATUSES,
    "curtailment_type": ODSE_CURTAILMENT_TYPES,
}

# Backward-compatible alias: the old name used by the SDK before v1.1
# (some callers may reference ODSE_ALLOWED_FIELDS directly)
