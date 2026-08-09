# <img src="https://raw.githubusercontent.com/AsobaCloud/sdk/main/docs/asoba-logo.svg" alt="Asoba" width="36" height="36" align="bottom" /> Ona SDK

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python CI](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml)
[![JavaScript CI](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml)

Live APIs for energy asset data across solar PV, wind, battery storage (BESS), and grid meters — with ODS-E (Open Data Schema for Energy) standardization covering market settlement, wheeling, tariffs, renewable certificates, and conformance profiles for SA trading workflows.

## What's included

### Core APIs
- **Inverter Telemetry** — query historical and stream live inverter data (5-min and daily resolution) for solar, wind and BESS
- **OODA Terminal Alerts** — query historical and stream live OODA fault/diagnostic alerts from terminal devices
- **Partner API** — fetch pre-computed JSON snapshots (KPIs, maintenance signals, forecasts, and preventive-maintenance schedules) with sub-100ms response times via ETag caching

### Advanced Services
- **Terminal API** — complete OODA workflow (Observe, Orient, Decide, Act) for asset management, fault detection, diagnostics, and scheduling
- **Energy Analyst** — RAG-based energy policy analysis and compliance queries
- **Edge Device Registry** — manage and monitor edge devices
- **Data Ingestion** — collect and process data from various sources
- **Weather Services** — cached weather data for forecasting
- **Interpolation Services** — fill missing data intervals
- **Standardization Services** — transform vendor-specific data to ODS-E standard

### Vendor-Specific Clients
- **Enphase Client** — data collection from Enphase Envoy systems
- **Huawei Client** — data collection from Huawei FusionSolar systems

### ML & Analytics
- **Global Training** — trigger and manage ML model training jobs
- **Gap Detection** — identify missing data intervals and trigger backfill
- **Freemium Forecasting** — CSV-based solar forecasting (no API key required)

### Data Standards
- **ODS-E Data Validation (Python)** — client-side validation against the full 65-field energy-timeseries schema with 6 conformance profiles (bilateral, wheeling, sawem_brp, municipal_recon, bess_dispatch, wind_scada)
- **Battery Health & Warranty Tracking** — monitor battery State of Health (SOH), capacity, and track warranty expiry via date or throughput limits
- **Resumable streaming** with cursor tokens for telemetry and alerts
- **Built-in rate limiting** and cost protection

---

## Quick Start

### 1. Get an API Key
Contact **support@asoba.co** to get an API key.

### 2. Install the SDK

**JavaScript:**
```bash
npm install @asobacloud/sdk
```

Or from source:
```bash
git clone https://github.com/AsobaCloud/sdk.git
cd sdk/javascript
npm install
```

**Python:**
```bash
pip install asoba
```

Or from source:
```bash
git clone https://github.com/AsobaCloud/sdk.git
cd sdk/python
pip3 install -e .
```

### 3. Set Environment Variables

```bash
export ASOBA_API_KEY=<your_api_key>
```

One key works for all APIs. Endpoint URLs are built into the SDK.

### 4. Test It Works

**JavaScript:**
```bash
cd javascript
node examples/inverter-telemetry-example.js
node examples/ooda-terminal-example.js
node examples/partner-api-example.js
node examples/terminal-api-example.js
node examples/edge-device-example.js
node examples/forecasting-example.js
node examples/freemium-forecast-example.js
```

**Python:**
```bash
cd python
python3 examples/inverter_telemetry_example.py
python3 examples/ooda_terminal_example.py
python3 examples/partner_api_example.py
python3 examples/terminal_ooda_example.py
python3 examples/edge_device_example.py
python3 examples/forecasting_example.py
python3 examples/freemium_forecast_example.py
python3 examples/complete_workflow_example.py
```

---

## Inverter Telemetry API

Query and stream live power output, energy, temperature, and state data from solar inverters.

### JavaScript
```javascript
const { OnaSDK } = require('./src/index');

const sdk = new OnaSDK();
// apiKey from ASOBA_API_KEY env var

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
from asoba import OnaClient

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

const sdk = new OnaSDK();
// apiKey from ASOBA_API_KEY env var

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
from asoba import OnaClient
from asoba.models.ooda import TimeRange

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

## Terminal API (OODA Workflow)

Complete asset management workflow including fault detection, diagnostics, scheduling, and ML model management.

### JavaScript
```javascript
const { OnaSDK } = require('./src/index');

const sdk = new OnaSDK();
// Requires authentication via terminal endpoint

// List assets
const assets = await sdk.terminal.listAssets({ customer_id: 'Sibaya' });

// Run fault detection
const detection = await sdk.terminal.runDetection({
  customer_id: 'Sibaya',
  asset_id: 'INV-001',
  lookback_hours: 6
});

// Run diagnostics
const diagnostic = await sdk.terminal.runDiagnostics({
  customer_id: 'Sibaya',
  asset_id: 'INV-001',
  detection_id: detection.detection_id
});

// Create maintenance schedule
const schedule = await sdk.terminal.createSchedule({
  customer_id: 'Sibaya',
  asset_id: 'INV-001',
  description: 'Replace inverter',
  priority: 'High',
  estimated_duration_hours: 8
});

// Get ML models
const models = await sdk.terminal.getMLModels();
```

### Python
```python
from asoba import OnaClient

client = OnaClient()

# Login required for Terminal API
client.auth.login("user@example.com", "password")

# List assets
assets = client.terminal.list_assets(customer_id='Sibaya')

# Run fault detection
detection = client.terminal.run_detection(
    customer_id='Sibaya',
    asset_id='INV-001',
    lookback_hours=6
)

# Run diagnostics
diagnostic = client.terminal.run_diagnostics(
    customer_id='Sibaya',
    asset_id='INV-001',
    detection_id=detection['detection_id']
)

# Create maintenance schedule
schedule = client.terminal.create_schedule(
    customer_id='Sibaya',
    asset_id='INV-001',
    description='Replace inverter',
    priority='High',
    estimated_duration_hours=8
)

# Get ML models
models = client.terminal.get_ml_models()
```

---

## Energy Analyst API

RAG-based energy policy analysis and compliance queries.

### JavaScript
```javascript
const answer = await sdk.energyAnalyst.query({
  question: 'What are the grid code requirements for solar installations?',
  n_results: 3
});
console.log(`Answer: ${answer.answer}`);
console.log(`Citation: ${answer.citation}`);
```

### Python
```python
answer = client.energy_analyst.query(
    question='What are the grid code requirements for solar installations?',
    n_results=3
)
print(f"Answer: {answer['answer']}")
print(f"Citation: {answer['citation']}")
```

---

## Edge Device Management

Manage and monitor edge devices in the field.

### JavaScript
```javascript
// List all devices
const devices = await sdk.edgeRegistry.getDevices();

// Get device details
const device = await sdk.edgeRegistry.getDevice({ device_id: 'EDGE-001' });

// Update device status
await sdk.edgeRegistry.updateDevice({
  device_id: 'EDGE-001',
  status: 'online'
});
```

### Python
```python
# List all devices
devices = client.edge_devices.get_devices()

# Get device details
device = client.edge_devices.get_device(device_id='EDGE-001')

# Update device status
client.edge_devices.update_device(
    device_id='EDGE-001',
    status='online'
)
```

---

## Forecasting Services

### Internal Forecasting (JavaScript)
```javascript
const forecast = await sdk.forecasting.getSiteForecast({
  site_id: 'Sibaya',
  forecast_hours: 24
});
console.log(`Forecast generated at: ${forecast.generated_at}`);
```

### Freemium Forecasting (No API Key Required)
```javascript
const forecast = await sdk.freemiumForecast.getForecast({
  site_id: 'Sibaya',
  hours: 24
});
```

```python
# Python
forecast = client.freemium_forecast.get_forecast(
    site_id='Sibaya',
    hours=24
)
```

---

## Advanced ML Services

Trigger model training, detect data gaps, and manage ML workflows.

### Gap Detection
```python
# Python
from asoba import OnaClient

client = OnaClient()

results = client.gap_detection.detect_gaps(
    customer_id='Sibaya',
    lookback_days=7,
    min_gap_minutes=15
)

if results.get('needs_backfill'):
    print(f"Missing intervals: {results['total_missing_intervals']}")
```

### Global Training
```python
# Python
# Start a training job
result = client.training.start_training(
    model_type='fault_detection',
    training_data_key='s3://bucket/training-data.csv',
    model_params={'epochs': 100}
)

# Check status
status = client.training.get_training_status(job_id=result['job_id'])
print(f"Training status: {status['status']}")

# List models
models = client.training.list_models()
```

---

## Partner API

Fetch pre-computed JSON snapshots for embedding and partner integrations. This API is optimized for speed using ETag-based conditional GETs and in-memory caching.

### JavaScript
```javascript
const { OnaSDK } = require('./src/index');

const sdk = new OnaSDK();
// apiKey from ASOBA_API_KEY env var

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
from asoba import OnaClient

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
from asoba import OnaClient
from asoba.utils.validation import validate_odse_record, validate_with_profile, validate_batch
from asoba.models.odse import ODSE_REQUIRED_FIELDS, ODSE_ALLOWED_FIELDS, ODSE_PROFILES

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
from asoba.utils.validation import validate_with_profile

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

## Data Ingestion & Standardization

Collect data from various sources and transform vendor-specific formats to ODS-E standard.

### Data Ingestion
```javascript
// Ingest data from external sources
const result = await sdk.dataIngestion.ingestData({
  source: 'enphase',
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01', end: '2025-11-02' }
});
```

```python
# Python
result = client.data_ingestion.ingest_data(
    source='enphase',
    site_id='Sibaya',
    time_range={'start': '2025-11-01', 'end': '2025-11-02'}
)
```

### Standardization
```python
# Transform vendor data to ODS-E standard
standardized = client.standardization.transform_to_odse(
    vendor_data=raw_data,
    source_system='huawei-fusionsolar'
)
```

### Vendor-Specific Clients
```javascript
// Enphase data collection
const enphaseData = await sdk.enphase.getData({
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01', end: '2025-11-02' }
});

// Huawei data collection
const huaweiData = await sdk.huawei.getData({
  plant_id: 'PLANT-001',
  time_range: { start: '2025-11-01', end: '2025-11-02' }
});
```

```python
# Python
# Enphase data collection
enphase_data = client.enphase.get_data(
    site_id='Sibaya',
    time_range={'start': '2025-11-01', 'end': '2025-11-02'}
)

# Huawei data collection
huawei_data = client.huawei.get_data(
    plant_id='PLANT-001',
    time_range={'start': '2025-11-01', 'end': '2025-11-02'}
)
```

---

## Weather & Interpolation Services

### Weather Services
```javascript
// Get cached weather data
const weather = await sdk.weather.getWeather({
  location: 'Durban',
  date: '2025-11-01'
});
```

```python
# Python
weather = client.weather.get_weather(
    location='Durban',
    date='2025-11-01'
)
```

### Interpolation Services
```javascript
// Fill missing data intervals
const interpolated = await sdk.interpolation.interpolate({
  data: partial_data,
  method: 'linear',
  max_gap_minutes: 30
});
```

```python
# Python
interpolated = client.interpolation.interpolate(
    data=partial_data,
    method='linear',
    max_gap_minutes=30
)
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

### Terminal API (OODA Workflow) Methods
|| Method | Description |
||--------|-------------|
|| `listAssets` / `list_assets` | List all assets for a customer |
|| `runDetection` / `run_detection` | Run fault detection on an asset |
|| `runDiagnostics` / `run_diagnostics` | Run diagnostics on a detection result |
|| `createSchedule` / `create_schedule` | Create maintenance schedule |
|| `listActivities` / `list_activities` | List recent activities |
|| `getMLModels` / `get_ml_models` | Get registered ML models |
|| `getNowcastData` / `get_nowcast_data` | Get current site metrics |

### Energy Analyst Methods
|| Method | Description |
||--------|-------------|
|| `query` / `query` | Query energy policy and compliance information |

### Edge Device Registry Methods
|| Method | Description |
||--------|-------------|
|| `getDevices` / `get_devices` | List all edge devices |
|| `getDevice` / `get_device` | Get device details |
|| `updateDevice` / `update_device` | Update device status |

### Forecasting Methods
|| Method | Description |
||--------|-------------|
|| `getSiteForecast` / `get_site_forecast` | Get internal forecast (requires credentials) |
|| `getForecast` / `get_forecast` | Get freemium forecast (no API key required) |

### ML & Analytics Methods
|| Method | Description |
||--------|-------------|
|| `detectGaps` / `detect_gaps` | Detect missing data intervals |
|| `startTraining` / `start_training` | Start ML model training job |
|| `getTrainingStatus` / `get_training_status` | Get training job status |
|| `listModels` / `list_models` | List trained models |

### Data Ingestion & Standardization Methods
|| Method | Description |
||--------|-------------|
|| `ingestData` / `ingest_data` | Ingest data from external sources |
|| `transformToOdse` / `transform_to_odse` | Transform vendor data to ODS-E standard |

### Vendor-Specific Methods
|| Method | Description |
||--------|-------------|
|| `getData` / `get_data` | Get data from vendor-specific systems (Enphase, Huawei) |

### Weather & Interpolation Methods
|| Method | Description |
||--------|-------------|
|| `getWeather` / `get_weather` | Get cached weather data |
|| `interpolate` / `interpolate` | Fill missing data intervals |

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
| Inverter Telemetry | `https://telemetry.api.asoba.co` |
| OODA Terminal Alerts | `https://ooda.api.asoba.co` |
| Partner API | `https://partner.api.asoba.co` |

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/missing API key | Check your API key with support@asoba.co |
| `403 Forbidden` | API key not scoped to site | Request access to the site_id you're querying |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry (60 req/min limit) |
| `ValidationError` | Invalid parameters | Check time ranges, limits, and required fields |
| `ConfigurationError` | Missing endpoint or API key | Verify environment variables are set |

**Debug Steps:**
1. Verify your API key is set: `echo $ASOBA_API_KEY`
2. Run the provided examples first — they test the full flow
3. Ensure you're querying a valid `site_id` (try `Sibaya` for testing)

---

## Repository Structure
```
sdk/
├── javascript/
│   ├── src/services/
│   │   ├── InverterTelemetryClient.js
│   │   ├── OodaTerminalClient.js
│   │   ├── PartnerApiClient.js
│   │   ├── TerminalClient.js
│   │   ├── EnergyAnalystClient.js
│   │   ├── EdgeDeviceRegistryClient.js
│   │   ├── DataIngestionClient.js
│   │   ├── WeatherClient.js
│   │   ├── InterpolationClient.js
│   │   ├── ForecastingClient.js
│   │   ├── FreemiumForecastClient.js
│   │   ├── EnphaseClient.js
│   │   ├── HuaweiClient.js
│   │   └── [utility files]
│   ├── src/types/index.d.ts
│   ├── examples/
│   │   ├── inverter-telemetry-example.js
│   │   ├── ooda-terminal-example.js
│   │   ├── partner-api-example.js
│   │   ├── terminal-api-example.js
│   │   ├── edge-device-example.js
│   │   ├── forecasting-example.js
│   │   └── freemium-forecast-example.js
│   └── tests/
│       ├── inverterTelemetry.test.js
│       ├── partnerApi.test.js
│       └── [other test files]
├── python/
│   ├── asoba/services/
│   │   ├── inverter_telemetry.py
│   │   ├── ooda_terminal.py
│   │   ├── partner_api.py
│   │   ├── terminal.py
│   │   ├── energy_analyst.py
│   │   ├── edge_device.py
│   │   ├── data_ingestion.py
│   │   ├── weather.py
│   │   ├── interpolation.py
│   │   ├── forecasting.py
│   │   ├── freemium_forecast.py
│   │   ├── standardization.py
│   │   ├── enphase.py
│   │   ├── huawei.py
│   │   ├── training.py
│   │   ├── gap_detection.py
│   │   └── [other services]
│   ├── asoba/utils/
│   │   ├── validation.py
│   │   └── [other utilities]
│   ├── asoba/models/
│   │   ├── odse.py
│   │   └── [other models]
│   ├── examples/
│   │   ├── inverter_telemetry_example.py
│   │   ├── ooda_terminal_example.py
│   │   ├── partner_api_example.py
│   │   ├── terminal_ooda_example.py
│   │   ├── edge_device_example.py
│   │   ├── forecasting_example.py
│   │   ├── freemium_forecast_example.py
│   │   └── complete_workflow_example.py
│   └── tests/
│       ├── test_client.py
│       ├── test_inverter_telemetry_client.py
│       ├── test_partner_api_client.py
│       ├── test_validation.py
│       └── [other test files]
└── backend/
    ├── inverter_telemetry_api/
    ├── ooda_terminal_api/
    └── partner_api/
```

---

## Support

**Need an API Key?** Contact **support@asoba.co** with your use case.

**Issues?** Open one at https://github.com/AsobaCloud/sdk/issues

**Email:** support@asoba.co

---

## License

MIT License
