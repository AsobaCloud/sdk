# Ona SDK

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python CI](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml)
[![JavaScript CI](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml)

## What Works Right Now

This SDK provides live APIs for energy asset data across solar PV, wind, battery storage (BESS), and grid meters — with ODS-E (Open Data Schema for Energy) standardization covering market settlement, wheeling, tariffs, renewable certificates, and conformance profiles for SA trading workflows.

**✅ Working Features:**
- **Inverter Telemetry** — query historical and stream live inverter data (5-min and daily resolution)
- **OODA Terminal Alerts** — query historical and stream live OODA fault/diagnostic alerts from terminal devices
- **Battery Health & Warranty Tracking** — monitor battery State of Health (SOH), capacity, and track warranty expiry via date or throughput limits
- **Partner API** — fetch pre-computed JSON snapshots (KPIs, maintenance signals, forecasts, and preventive-maintenance schedules) with sub-100ms response times via ETag caching
- **ODS-E Data Validation (Python)** — client-side validation against the full 65-field energy-timeseries schema with 6 conformance profiles (bilateral, wheeling, sawem_brp, municipal_recon, bess_dispatch, wind_scada)
- Resumable streaming with cursor tokens for telemetry and alerts
- Built-in rate limiting and cost protection

**🚧 Planned Features:**
- Solar Energy Forecasting (Working)
- Wind & BESS telemetry streaming
- Energy Policy Analysis
- Edge Device Management (Working)
- Data Collection integrations

---

## Quick Start

### 1. Get an API Key
Contact **support@asoba.org** to get an API key.

### 2. Install the SDK

**JavaScript:**
```bash
git clone https://github.com/AsobaCloud/sdk.git
cd sdk/javascript
npm install
```

**Python:**
```bash
git clone https://github.com/AsobaCloud/sdk.git
cd sdk/python
pip3 install -e .
```

### 3. Set Environment Variables

**Inverter Telemetry:**
```bash
export INVERTER_TELEMETRY_ENDPOINT=https://af5jy5ob3e.execute-api.af-south-1.amazonaws.com/prod
export INVERTER_TELEMETRY_API_KEY=<your_api_key>
```

**OODA Terminal Alerts:**
```bash
export OODA_TERMINAL_ENDPOINT=https://3lpq00xevg.execute-api.af-south-1.amazonaws.com/prod
export OODA_TERMINAL_API_KEY=<your_api_key>
```

**Partner API:**
```bash
export PARTNER_API_ENDPOINT=https://8el3o25tc1.execute-api.af-south-1.amazonaws.com/prod
export PARTNER_API_KEY=<your_api_key>
```

> The same API key works for all endpoints — just set it in the respective variables.

### 4. Test It Works

**JavaScript:**
```bash
cd javascript
node examples/inverter-telemetry-example.js
node examples/ooda-terminal-example.js
node examples/partner-api-example.js
```

**Python:**
```bash
cd python
python3 examples/inverter_telemetry_example.py
python3 examples/ooda_terminal_example.py
python3 examples/partner_api_example.py
```

---

## Inverter Telemetry API

Query and stream live power output, energy, temperature, and state data from solar inverters.

### JavaScript
```javascript
const { OnaSDK } = require('./src/index');

const sdk = new OnaSDK({
  endpoints: {
    inverterTelemetry: process.env.INVERTER_TELEMETRY_ENDPOINT,
  },
  inverterTelemetryApiKey: process.env.INVERTER_TELEMETRY_API_KEY,
});

// Query historical data
const records = await sdk.inverterTelemetry.getInverterTelemetry({
  asset_id: 'INV-1000000054495190',
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
  resolution: '5min',
  limit: 100,
});

// Stream live data
for await (const record of sdk.inverterTelemetry.streamInverter({
  asset_id: 'INV-1000000054495190',
  site_id: 'Sibaya',
  polling_interval: 30,
})) {
  console.log(`${record.timestamp}: ${record.power} kW`);
}
```

### Python
```python
from ona_platform import OnaClient

client = OnaClient()

# Query historical data
records = client.inverter_telemetry.get_inverter_telemetry(
    asset_id='INV-1000000054495190',
    site_id='Sibaya',
    time_range={'start': '2025-11-01T00:00:00', 'end': '2025-11-01T12:00:00'},
    resolution='5min',
    limit=100,
)

# Stream live data
for record in client.inverter_telemetry.stream_inverter(
    asset_id='INV-1000000054495190',
    site_id='Sibaya',
    polling_interval=30,
):
    print(f"{record.timestamp}: {record.power} kW")
```

---

## OODA Terminal Alerts API

Query and stream OODA (Observe, Orient, Decide, Act) fault detection and diagnostic alerts from terminal devices.

### JavaScript
```javascript
const { OnaSDK } = require('./src/index');

const sdk = new OnaSDK({
  endpoints: {
    oodaTerminal: process.env.OODA_TERMINAL_ENDPOINT,
  },
  oodaTerminalApiKey: process.env.OODA_TERMINAL_API_KEY,
});

// Query historical alerts
const alerts = await sdk.oodaTerminal.getTerminalAlerts({
  terminal_device_id: 'TERM-1000000054495190',
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
  resolution: '5min',
  limit: 100,
});

// Query all terminal devices at a site
const siteAlerts = await sdk.oodaTerminal.getSiteAlerts({
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
});

// Discover available data range
const period = await sdk.oodaTerminal.getDataPeriod({ site_id: 'Sibaya' });
console.log(`Data from ${period.first_record} to ${period.last_record}`);

// Stream live alerts
for await (const alert of sdk.oodaTerminal.streamTerminal({
  terminal_device_id: 'TERM-1000000054495190',
  site_id: 'Sibaya',
  polling_interval: 30,
})) {
  console.log(`${alert.timestamp}: [${alert.alert_severity}] ${alert.message}`);
}
```

### Python
```python
from ona_platform import OnaClient
from ona_platform.models.ooda import TimeRange

client = OnaClient()

# Query historical alerts
alerts = client.ooda_terminal.get_terminal_alerts(
    terminal_device_id='TERM-1000000054495190',
    site_id='Sibaya',
    time_range=TimeRange(start='2025-11-01T00:00:00', end='2025-11-01T12:00:00'),
    resolution='5min',
    limit=100,
)

# Query all terminal devices at a site
site_alerts = client.ooda_terminal.get_site_alerts(
    site_id='Sibaya',
    time_range=TimeRange(start='2025-11-01T00:00:00', end='2025-11-01T12:00:00'),
)

# Discover available data range
period = client.ooda_terminal.get_data_period(site_id='Sibaya')
print(f"Data from {period.first_record} to {period.last_record}")

# Stream live alerts
for alert in client.ooda_terminal.stream_terminal(
    terminal_device_id='TERM-1000000054495190',
    site_id='Sibaya',
    polling_interval=30,
):
    print(f"{alert.timestamp}: [{alert.alert_severity}] {alert.message}")
```

---

## Advanced ML Services

Trigger model training, detect data gaps, and manage edge devices directly via the SDK.

### Gap Detection
```javascript
const results = await sdk.gapDetection.detectGaps({ customer_id: 'Sibaya' });
if (results.needs_backfill) {
  console.log(`Missing intervals: ${results.total_missing_intervals}`);
}
```

### Global Training
```python
# Trigger a new training job
client.training.trigger_training(customer_id='Sibaya', promote=True)

# Check status
status = client.training.get_training_status(customer_id='Sibaya')
print(f"Training status: {status['status']}")
```

---

## Partner API

Fetch pre-computed JSON snapshots for embedding and partner integrations. This API is optimized for speed using ETag-based conditional GETs and in-memory caching.

> **Config note (Python):** `partner_api_endpoint` must use `https://` — the SDK raises `ConfigurationError` on init if it doesn't. Set via `PARTNER_API_ENDPOINT` env var or the `OnaConfig(partner_api_endpoint=...)` dataclass field. The `partner_api_key` is sent as the `x-api-key` header.

### JavaScript
```javascript
const { OnaSDK } = require('./src/index');

const sdk = new OnaSDK({
  endpoints: {
    partnerApi: process.env.PARTNER_API_ENDPOINT,
  },
  partnerApiKey: process.env.PARTNER_API_KEY,
});

// 1. KPI rollup (first call: full fetch; second call: returns cached if ETag matches)
const kpis = await sdk.partner.getKpiRollup({ site_id: 'Sibaya' });
const cachedKpis = await sdk.partner.getKpiRollup({ site_id: 'Sibaya' });

// 2. Maintenance signals (detected anomalies) — optional `since` and `severity` filters
const signals = await sdk.partner.getMaintenanceSignals({
  site_id: 'Sibaya',
  since: '2025-11-01T00:00:00',
  severity: 'high',
});

// 3. Forecast snapshot — pre-computed 24h solar forecast (optional `horizon`)
const forecast = await sdk.partner.getForecastSnapshot({ site_id: 'Sibaya' });
console.log(`Forecast horizon: ${forecast.horizon_hours}h, intervals: ${forecast.intervals.length}`);

// 4. Maintenance schedule (90-day preventive tasks) — SEP-062
const schedule = await sdk.partner.getMaintenanceSchedule({ site_id: 'Sibaya' });
console.log(`Tasks: ${schedule.summary.total_tasks}`);
for (const task of schedule.tasks) {
  console.log(`  ${task.recommended_date} — ${task.asset_id} — ${task.task_type} (${task.priority})`);
}
```

### Python
```python
from ona_platform import OnaClient

client = OnaClient()

# 1. KPI rollup (first call: full fetch; second call: returns cached if ETag matches)
kpis = client.partner.get_kpi_rollup(site_id='Sibaya')
cached_kpis = client.partner.get_kpi_rollup(site_id='Sibaya')

# 2. Maintenance signals (detected anomalies) — optional `since` and `severity` filters
signals = client.partner.get_maintenance_signals(
    site_id='Sibaya',
    since='2025-11-01T00:00:00',
    severity='high',
)

# 3. Forecast snapshot — pre-computed 24h solar forecast (optional `horizon`)
forecast = client.partner.get_forecast_snapshot(site_id='Sibaya')
print(f"Forecast horizon: {forecast['horizon_hours']}h, intervals: {len(forecast['intervals'])}")

# 4. Maintenance schedule (90-day preventive tasks) — SEP-062
schedule = client.partner.get_maintenance_schedule(site_id='Sibaya')
print(f"Tasks: {schedule['summary']['total_tasks']}")
for task in schedule['tasks']:
    print(f"  {task['recommended_date']} — {task['asset_id']} — {task['task_type']} ({task['priority']})")
```

### KPI Rollup Snapshot Structure

The `getKpiRollup` / `get_kpi_rollup` method returns a nested `KpiRollupSnapshot` with typed sub-objects. The Python SDK exposes these as dataclasses (`EarKpis`, `FinancialKpis`); the JavaScript SDK exposes them as TypeScript interfaces.

**Top-level fields:**

| Field | Type | Description |
|-------|------|-------------|
| `site_id` | string | Site identifier |
| `period` | `{ start, end }` | Reporting period (ISO dates) |
| `generated_at` | string (ISO timestamp) | When the snapshot was generated |
| `system` | `{ rated_capacity_kw, device_count }` | System metadata |
| `energy_balance` | `{ consumption_kwh, solar_production_kwh, grid_purchases_kwh, solar_offset_pct }` | Energy balance metrics |
| `performance` | `{ system_pr, pr_target, pr_status, true_uptime_pct, state_uptime_pct, availability_pct, availability_target }` | Performance ratio and uptime |
| `ear` | `EarKpis` | Energy-at-risk and recovery KPIs (see below) |
| `financial` | `FinancialKpis` | Financial metrics in site tariff currency (see below) |
| `battery` | object (optional) | Battery health KPIs (`avg_soc`, `avg_soh`, `total_capacity_kwh`, `warranty_status`, `throughput_kwh`) — present only for sites with battery assets |

**`EarKpis` — Energy-at-Risk & Recovery:**

| Field | Type | Description |
|-------|------|-------------|
| `energy_lost_kwh` | float | Energy lost (kWh) over the period |
| `energy_lost_pct` | float | Energy lost as % of expected |
| `capacity_utilization_pct` | float | Capacity utilization (%) |
| `recovery_potential_kwh` | `{ "50pct", "75pct", "100pct" }` | Recoverable kWh at 50/75/100% recovery |
| `value_lost_zar` | float | Value of lost energy (ZAR) |
| `realized_savings_zar` | float | Realized savings (ZAR) |
| `annual_projection_zar` | float | Annualized projection (ZAR) |

**`FinancialKpis` — Financial Metrics:**

| Field | Type | Description |
|-------|------|-------------|
| `tariff_currency` | string | Tariff currency code (e.g. `ZAR`) |
| `shortfall_cost_zar` | float | Cost of energy shortfall (ZAR) |
| `realized_savings_zar` | float | Realized savings vs grid (ZAR) |
| `total_potential_value_zar` | float | Total potential value (shortfall + savings, ZAR) |
| `tou_breakdown` | object | Time-of-Use tariff breakdown by period |

**TypeScript types** (JavaScript SDK, `src/types/index.d.ts`): `EarKpis`, `FinancialKpis`, `KpiRollupSnapshot`, and `PartnerApiClient` are exported. The SDK client exposes `sdk.partner: PartnerApiClient`.

---

## ODS-E Data Standard

The Ona SDK uses [ODS-E (Open Data Schema for Energy)](https://github.com/AsobaCloud/ona-protocol) — an open specification for interoperable energy asset data across generation, consumption, net metering, market settlement, wheeling, and certificate tracking. The full schema lives in [`ona-protocol/schemas/energy-timeseries.json`](https://github.com/AsobaCloud/ona-protocol/blob/main/schemas/energy-timeseries.json).

### Energy Timeseries Fields (65)

The `energy-timeseries` schema defines 65 optional fields (3 required: `timestamp`, `kWh`, `error_type`). Fields are grouped by domain:

#### Core Telemetry
| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string (date-time) | ISO 8601 timestamp with timezone **(required)** |
| `kWh` | number | Active energy in kWh **(required)** |
| `error_type` | enum | `normal`, `warning`, `critical`, `fault`, `offline`, `standby`, `unknown` **(required)** |
| `error_code` | string | Original OEM error code |
| `kVArh` | number | Reactive energy |
| `kVA` | number | Apparent power (min 0) |
| `PF` | number | Power factor (0–1) |
| `direction` | enum | `generation`, `consumption`, `net` |

#### End-Use & Fuel
| Field | Type | Description |
|-------|------|-------------|
| `end_use` | enum | ComStock/ResStock end-use category (cooling, heating, pv_generation, battery_storage, etc.) |
| `fuel_type` | enum | `electricity`, `natural_gas`, `propane`, `fuel_oil`, `other` |

#### Market Settlement
| Field | Type | Description |
|-------|------|-------------|
| `seller_party_id` | string | Canonical seller ID (`authority:type:id`) |
| `buyer_party_id` | string | Canonical buyer ID |
| `network_operator_id` | string | Network operator ID |
| `wheeling_agent_id` | string | Wheeling intermediary ID |
| `settlement_period_start` | date-time | Settlement window start |
| `settlement_period_end` | date-time | Settlement window end |
| `loss_factor` | number | Applied loss factor (e.g. 0.03 for 3%) |
| `contract_reference` | string | PPA / bilateral / wheeling schedule ref |

#### Tariff
| Field | Type | Description |
|-------|------|-------------|
| `tariff_schedule_id` | string | Canonical tariff ID (`authority:municipality:code:vN`) |
| `tariff_period` | enum | `peak`, `standard`, `off_peak`, `critical_peak` |
| `tariff_currency` | string | ISO 4217 currency code (e.g. `ZAR`) |
| `tariff_version_effective_at` | date-time | Tariff version effective timestamp |
| `energy_charge_component` | number | Energy charge for this interval |
| `network_charge_component` | number | Network charge for this interval |

#### Wheeling
| Field | Type | Description |
|-------|------|-------------|
| `wheeling_type` | enum | `traditional`, `virtual`, `portfolio` |
| `injection_point_id` | string | Grid injection point |
| `offtake_point_id` | string | Grid offtake point |
| `wheeling_status` | enum | `provisional`, `confirmed`, `reconciled`, `disputed` |
| `wheeling_path_id` | string | Registered wheeling path reference |

#### Unbundled Charges
| Field | Type | Description |
|-------|------|-------------|
| `generation_charge_component` | number | Generation charge |
| `transmission_charge_component` | number | Transmission use-of-system charge |
| `distribution_charge_component` | number | Distribution network charge |
| `ancillary_service_charge_component` | number | Ancillary services levy |
| `non_bypassable_charge_component` | number | Cross-subsidies, FBE contributions |
| `environmental_levy_component` | number | Environmental / carbon levy |

#### Curtailment
| Field | Type | Description |
|-------|------|-------------|
| `curtailment_flag` | boolean | Whether generation was curtailed |
| `curtailment_type` | enum | `congestion`, `frequency`, `voltage`, `instruction`, `other` |
| `curtailed_kWh` | number | Estimated generation lost (min 0) |
| `curtailment_instruction_id` | string | System operator dispatch instruction ref |

#### Balance Responsibility
| Field | Type | Description |
|-------|------|-------------|
| `balance_responsible_party_id` | string | BRP ID for this connection point |
| `forecast_kWh` | number | Nominated/scheduled volume |
| `imbalance_kWh` | number | Forecast vs actual (positive = over-delivery) |
| `settlement_type` | enum | `bilateral`, `sawem_day_ahead`, `sawem_intra_day`, `balancing`, `ancillary` |

#### Billing
| Field | Type | Description |
|-------|------|-------------|
| `billing_period` | string | Billing cycle reference (e.g. `2026-02`, `2026-W07`) |
| `billed_kWh` | number | Billed quantity (may differ from metered) |
| `billing_status` | enum | `metered`, `estimated`, `adjusted`, `disputed` |
| `daa_reference` | string | Distribution Agency Agreement reference |

#### Renewable Certificates
| Field | Type | Description |
|-------|------|-------------|
| `renewable_attribute_id` | string | Certificate/credit ID (e.g. I-REC tracking number) |
| `certificate_standard` | enum | `i_rec`, `rego`, `go`, `rec`, `tigr`, `other` |
| `verification_status` | enum | `pending`, `issued`, `retired`, `cancelled` |
| `carbon_intensity_gCO2_per_kWh` | number | Carbon intensity (g CO2e / kWh) |

#### BESS — Battery Energy Storage (SEP-026)
| Field | Type | Description |
|-------|------|-------------|
| `soc` | number | State of charge (0–100) |
| `soh` | number | State of health (0–100) |
| `charge_kWh` | number | Energy charged this interval (min 0) |
| `discharge_kWh` | number | Energy discharged this interval (min 0) |
| `cycle_count` | number | Cumulative charge/discharge cycles |
| `cell_temp_min_c` | number | Min cell temperature (°C) |
| `cell_temp_max_c` | number | Max cell temperature (°C) |
| `cell_voltage_min_v` | number | Min cell voltage (V) |
| `cell_voltage_max_v` | number | Max cell voltage (V) |
| `dispatch_mode` | enum | `charging`, `discharging`, `standby`, `balancing` |

#### Wind Turbine SCADA (SEP-025)
| Field | Type | Description |
|-------|------|-------------|
| `wind_speed_ms` | number | Wind speed (m/s, min 0) |
| `rotor_rpm` | number | Rotor revolutions per minute |
| `blade_pitch_deg` | number | Blade pitch angle (degrees) |
| `nacelle_direction_deg` | number | Nacelle orientation (0–360 compass bearing) |

### Asset Metadata Schema

The [`asset-metadata.json`](https://github.com/AsobaCloud/ona-protocol/blob/main/schemas/asset-metadata.json) schema defines asset configuration and location:

| Field | Type | Description |
|-------|------|-------------|
| `asset_id` | string | Unique asset identifier (required) |
| `location` | object | `{ latitude, longitude, timezone, region, country_code, municipality_id, distribution_zone, feeder_id, voltage_level, meter_id, connection_point_id, ... }` (required: lat/lon/tz) |
| `capacity_kw` | number | Nameplate power capacity (required) |
| `capacity_kwh` | number | Nameplate energy storage capacity |
| `oem` | string | Original equipment manufacturer (required) |
| `model` | string | Equipment model identifier |
| `serial_number` | string | Manufacturer serial number |
| `commissioning_date` | date | ISO 8601 commissioning date |
| `ppa_id` | string | Associated power purchase agreement |
| `asset_type` | enum | `solar_pv`, `wind_turbine`, `battery_storage`, `grid_meter`, `ev_charger`, `hvac_system`, `generator`, `chp`, `fuel_cell`, `other` |
| `building` | object | ComStock/ResStock building metadata (building_type, climate_zone, vintage, floor_area_sqm) |

### Additional Schemas (8)

| Schema | Purpose | Key Fields |
|--------|---------|------------|
| `equipment-register.json` | Equipment hierarchy registry | equipment_id, site_id, equipment_type, manufacturer, model, install_date, warranty_expiry |
| `equipment-id-map.json` | Source-to-canonical ID mapping | source_equipment_id, equipment_id |
| `maintenance-history.json` | Work order and maintenance records | work_order_id, equipment_id, failure_code, cause_code, downtime_hours, parts_consumed |
| `spare-parts.json` | Spare parts inventory | part_id, qty_on_hand, qty_reserved, reorder_point, supplier_lead_time_days |
| `failure-taxonomy.json` | Standardized failure classification | failure_code, cause_code, recurrence_rate, typical_mttr_hours |
| `procurement-context.json` | Procurement and supplier context | part_id, preferred_supplier, avg_lead_time_days, open_po_eta |
| `regulatory-event.json` | Regulatory event normalization | event_type, jurisdiction, regulator, effective_date, deadline_date |
| `alarm-frequency-profile.json` | Alarm frequency and escalation | alarm_code, count_7d, count_30d, count_90d, escalation_rate, mean_time_between_alarms_hours |

### Conformance Profiles (6)

Profiles are a validator-level concept layered on top of the schema. They specify which fields must be present for a given operating context. Use `validate_with_profile()` to apply them.

| Profile | Use Case | Required Fields |
|---------|----------|-----------------|
| `bilateral` | PPA / bilateral trade settlement | seller_party_id, buyer_party_id, settlement_period_start/end, contract_reference, settlement_type=`bilateral` |
| `wheeling` | Wheeled energy across networks | All bilateral fields + network_operator_id, wheeling_type, injection/offtake_point_id, wheeling_status, loss_factor |
| `sawem_brp` | Wholesale market (SAWEM) settlement for BRPs | seller_party_id, balance_responsible_party_id, settlement_type (sawem_*), forecast_kWh, settlement_period_start/end |
| `municipal_recon` | Municipal billing / reconciliation | buyer_party_id, billing_period, billed_kWh, billing_status |
| `bess_dispatch` | BESS dispatch validation (SEP-026) | dispatch_mode, soc |
| `wind_scada` | Wind turbine SCADA validation (SEP-025) | wind_speed_ms |

### Vendor Transforms (20)

ODS-E includes transforms that convert vendor-specific data into the canonical schema:

| Asset Type | Vendor | Source Key | Transform Spec |
|------------|--------|------------|----------------|
| Solar PV | Huawei FusionSolar | `huawei-fusionsolar` | `transforms/huawei-fusionsolar.yaml` |
| Solar PV | Enphase Envoy | `enphase-envoy` | `transforms/enphase-envoy.yaml` |
| Solar PV | Fronius Solar API | `fronius-solar-api` | `transforms/fronius-solar-api.yaml` |
| Solar PV | SMA Monitoring | `sma-monitoring-api` | `transforms/sma-monitoring-api.yaml` |
| Solar PV | SolarEdge Monitoring | `solaredge-monitoring` | `transforms/solaredge-monitoring.yaml` |
| Solar PV | Solarman Logger | `solarman-logger` | `transforms/solarman-logger.yaml` |
| Solar PV | Solax Cloud API v2 | `solaxcloud-api-v2` | `transforms/solaxcloud-api-v2.yaml` |
| Solar PV | Solis Cloud API | `soliscloud-api` | `transforms/soliscloud-api.yaml` |
| Solar PV | Sungrow iSolarCloud | `sungrow-isolarcloud-api` | `transforms/sungrow-isolarcloud-api.yaml` |
| BESS | Sungrow PowerTitan | `sungrow_bess` | `transforms/sungrow-powertitan.yaml` |
| BESS | BYD BatteryBox | `byd_bess` | `transforms/byd-bess.yaml` |
| Wind | Vestas Online | `vestas` | `transforms/vestas-online.yaml` |
| Wind | Siemens Gamesa | `siemens_gamesa` | `transforms/siemens-gamesa-diagnostic.yaml` |
| Wind | Nordex Control | `nordex` | `transforms/nordex-control.yaml` |
| Meter | Switch Meter | `switch-meter` | `transforms/switch-meter.yaml` |
| Industrial | Higeco API | `higeco-api` | `transforms/higeco-api.yaml` |
| Industrial | Terraco Historian | `terraco-historian` | `transforms/terraco-historian.yaml` |
| Utility | Eskom AMR | `eskom-amr` | `transforms/eskom-amr.yaml` |
| Regulatory | Regulatory Events | `regulatory-events` | `transforms/regulatory-events-unified.yaml` |

---

## Data Ingestion Validation (Python SDK)

Validate records locally against the full ODS-E energy-timeseries schema (65 fields) before uploading to catch issues early. The SDK supports both basic schema validation and conformance profile validation.

```python
from ona_platform import OnaClient
from ona_platform.utils.validation import validate_odse_record, validate_with_profile, validate_batch
from ona_platform.models.odse import ODSE_REQUIRED_FIELDS, ODSE_ALLOWED_FIELDS, ODSE_PROFILES

client = OnaClient()

# Records to validate — full 65-field schema is supported
records = [
    {"timestamp": "2025-01-01T00:00:00Z", "kWh": 100.5, "error_type": "normal", "asset_id": "INV001"},
    {"timestamp": "invalid-date", "kWh": "not-a-number", "error_type": "unknown"},
]

# Validate locally (no service call)
result = validate_batch(records)

print(f"Valid: {result['summary']['valid']}/{result['summary']['total']}")

# Access valid records for upload
for record in result['valid_records']:
    print(f"Ready for upload: {record}")

# Review invalid records
for item in result['invalid_records']:
    print(f"Errors: {item['errors']}")
```

#### Conformance Profile Validation

For trading workflows (wheeling, bilateral, SAWEM, municipal reconciliation, BESS dispatch, wind SCADA), use `validate_with_profile()`:

```python
from ona_platform.utils.validation import validate_with_profile

# Bilateral trade settlement
bilateral_record = {
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
is_valid, errors, normalized = validate_with_profile(bilateral_record, "bilateral")

# BESS dispatch validation
bess_record = {
    "timestamp": "2026-06-27T10:00:00Z",
    "kWh": 50.0,
    "error_type": "normal",
    "dispatch_mode": "charging",
    "soc": 75.0,
}
is_valid, errors, normalized = validate_with_profile(bess_record, "bess_dispatch")

# Wind SCADA validation
wind_record = {
    "timestamp": "2026-06-27T10:00:00Z",
    "kWh": 320.0,
    "error_type": "normal",
    "wind_speed_ms": 8.5,
}
is_valid, errors, normalized = validate_with_profile(wind_record, "wind_scada")
```

Validation checks include: required fields, allowed field whitelist (65 fields), numeric bounds (BESS soc/soh 0–100, PF 0–1, nacelle 0–360, etc.), timestamp format, enum matching (13 enum-constrained fields), and conformance profile enforcement. The full schema is at [`ona-protocol/schemas/energy-timeseries.json`](https://github.com/AsobaCloud/ona-protocol/blob/main/schemas/energy-timeseries.json).

---

## Performance Intelligence & Battery Health

The Terminal API provides advanced intelligence for asset health, soiling analysis, and battery warranty tracking.

### Site Summary & Intelligence
Get high-level KPIs and automated analysis for a site.

#### JavaScript
```javascript
const summary = await sdk.terminal.getSiteSummary({ site_id: 'Sibaya' });

console.log(`Fleet PR: ${summary.fleet_pr_pct}%`);

// Soiling Analysis
if (summary.soiling) {
  console.log(`Soiling Rate: ${summary.soiling.soiling_rate_pct_day}%/day`);
  console.log(`Last Wash Gain: ${summary.soiling.recovery_gain_kwh_last_event} kWh`);
}

// Asset Prognostics
if (summary.prognostics) {
  console.log(`Health Score: ${summary.prognostics.health_score}/100`);
  console.log(`Est. Retirement: ${summary.prognostics.battery_retirement_date}`);
}
```

#### Python
```python
summary = client.terminal.get_site_summary(site_id='Sibaya')

print(f"Fleet PR: {summary['fleet_pr_pct']}%")

# Soiling Analysis
if 'soiling' in summary:
    soiling = summary['soiling']
    print(f"Soiling Rate: {soiling['soiling_rate_pct_day']}%/day")

# Battery Health (aggregated)
if 'battery' in summary:
    bat = summary['battery']
    print(f"Avg SOH: {bat['avg_soh']}%")
```

### Battery Warranty Tracking
Monitor individual battery assets and calculate remaining warranty life based on both date and throughput.

#### JavaScript
```javascript
// 1. Get asset with warranty details
const asset = await sdk.terminal.getAsset({ 
  customer_id: 'cust123', 
  asset_id: 'BAT-001' 
});

// 2. Calculate remaining warranty life
const status = sdk.terminal.constructor.calculateRemainingWarrantyLife({
  warranty_expiry_date: asset.warranty_expiry_date,
  warranty_throughput_kwh: asset.warranty_throughput_kwh,
  current_throughput_kwh: 5420.5 // From telemetry
});

console.log(`Warranty Status: ${status.warranty_status}`);
console.log(`Limiting Factor: ${status.limiting_factor}`);
```

#### Python
```python
# Calculate remaining warranty life
status = client.terminal.calculate_remaining_warranty_life(
    warranty_expiry_date='2030-12-31',
    warranty_throughput_kwh=10000.0,
    current_throughput_kwh=8500.0
)

print(f"Warranty Status: {status['warranty_status']}")
print(f"Throughput Remaining: {status['throughput_remaining_pct']}%")
```

---

## API Reference

### Inverter Telemetry Methods
| Method | Description |
|--------|-------------|
| `getInverterTelemetry` / `get_inverter_telemetry` | Historical data for a single inverter |
| `getSiteTelemetry` / `get_site_telemetry` | Historical data for all inverters at a site |
| `getDataPeriod` / `get_data_period` | Discover available data time range |
| `streamInverter` / `stream_inverter` | Stream live data from a single inverter |
| `streamSite` / `stream_site` | Stream live data from all inverters at a site |

### OODA Terminal Alert & Battery Methods
| Method | Description |
|--------|-------------|
| `getTerminalAlerts` / `get_terminal_alerts` | Historical alerts for a single terminal device |
| `getSiteAlerts` / `get_site_alerts` | Historical alerts for all terminal devices at a site |
| `getAsset` / `get_asset` | Get asset details (including battery capacity and warranty) |
| `getSiteSummary` / `get_site_summary` | Get site summary with battery health KPIs (SOH, SOC) |
| `getDataPeriod` / `get_data_period` | Discover available alert time range |
| `streamTerminal` / `stream_terminal` | Stream live alerts from a single terminal device |
| `streamSite` / `stream_site` | Stream live alerts from all terminal devices at a site |

### Advanced ML Services

Trigger model training, detect data gaps, and manage edge devices directly via the SDK.

### Gap Detection
```javascript
const results = await sdk.gapDetection.detectGaps({ customer_id: 'Sibaya' });
if (results.needs_backfill) {
  console.log(`Missing intervals: ${results.total_missing_intervals}`);
}
```

### Global Training
```python
# Trigger a new training job
client.training.trigger_training(customer_id='Sibaya', promote=True)

# Check status
status = client.training.get_training_status(customer_id='Sibaya')
print(f"Training status: {status['status']}")
```

---

## Partner API Methods
| Method | Description |
|--------|-------------|
| `getKpiRollup` / `get_kpi_rollup` | Site-level KPI summary snapshot (returns `KpiRollupSnapshot` with `EarKpis` + `FinancialKpis` sub-objects) |
| `getMaintenanceSignals` / `get_maintenance_signals` | Pending maintenance and health signals |
| `getForecastSnapshot` / `get_forecast_snapshot` | Pre-computed solar forecast snapshot |
| `getMaintenanceSchedule` / `get_maintenance_schedule` | Preventive-maintenance task list for the next 90 days (per inverter) |
| `getSnapshot` / `get_snapshot` | Generic snapshot fetch by kind |

### Shared Parameters
| Parameter | Description |
|-----------|-------------|
| `resolution` | `"5min"` (default) or `"daily"` |
| `limit` | Max records per query (default 100, max 1000) |
| `cursor` | Resume pagination from a previous position |
| `polling_interval` | Seconds between polls for streaming (min 5, default 5) |

### Rate Limits (all APIs)
- **60 requests per minute** per API key
- **Max 1000 records** per query
- **Max 31-day time range** per query
- **Min 5-second polling interval** for streaming

---

## Endpoints

| API | Endpoint |
|-----|----------|
| Inverter Telemetry | `https://af5jy5ob3e.execute-api.af-south-1.amazonaws.com/prod` |
| OODA Terminal Alerts | `https://3lpq00xevg.execute-api.af-south-1.amazonaws.com/prod` |
| Partner API | `https://8el3o25tc1.execute-api.af-south-1.amazonaws.com/prod` |

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/missing API key | Check your API key with support@asoba.org |
| `403 Forbidden` | API key not scoped to site | Request access to the site_id you're querying |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry (60 req/min limit) |
| `ValidationError` | Invalid parameters | Check time ranges, limits, and required fields |
| `ConfigurationError` | Missing endpoint or API key | Verify environment variables are set |

**Debug Steps:**
1. Verify all three env vars are set to the same API key:
   `echo $INVERTER_TELEMETRY_API_KEY` / `echo $OODA_TERMINAL_API_KEY` / `echo $PARTNER_API_KEY`
   (a single key value, exported under three names — see Quick Start §3)
2. Run the provided examples first — they test the full flow
3. Ensure you're querying a valid `site_id` (try `Sibaya` for testing)

---

## Repository Structure
```
sdk/
├── javascript/
│   ├── src/services/InverterTelemetryClient.js
│   ├── src/services/OodaTerminalClient.js
│   ├── src/services/PartnerApiClient.js
│   ├── src/types/index.d.ts          
│   ├── examples/inverter-telemetry-example.js
│   ├── examples/ooda-terminal-example.js
│   ├── examples/partner-api-example.js
│   └── tests/
│       ├── inverterTelemetry.test.js
│       └── partnerApi.test.js
├── python/
│   ├── ona_platform/services/inverter_telemetry.py
│   ├── ona_platform/services/ooda_terminal.py
│   ├── ona_platform/services/partner_api.py
│   ├── ona_platform/services/data_ingestion.py
│   ├── ona_platform/utils/validation.py
│   ├── ona_platform/models/odse.py
│   ├── examples/inverter_telemetry_example.py
│   ├── examples/ooda_terminal_example.py
│   ├── examples/partner_api_example.py
│   └── tests/
│       ├── test_client.py
│       ├── test_inverter_telemetry_client.py
│       ├── test_partner_api_client.py
│       └── test_validation.py
└── backend/
    ├── inverter_telemetry_api/   
    ├── ooda_terminal_api/        
    └── partner_api/              
```

---

## Support

**Need an API Key?** Contact **support@asoba.org** with your use case.

**Issues?** Open one at https://github.com/AsobaCloud/sdk/issues

**Email:** support@asoba.org

---

## License

MIT License
