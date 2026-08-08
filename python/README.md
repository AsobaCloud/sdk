# <img src="https://raw.githubusercontent.com/AsobaCloud/sdk/main/docs/asoba-logo.svg" alt="Asoba" width="36" height="36" align="bottom" /> Ona SDK — Python

[![PyPI](https://img.shields.io/pypi/v/asoba.svg)](https://pypi.org/project/asoba/)
[![CI](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Python SDK for live energy asset data — inverter telemetry, OODA terminal alerts, Partner API snapshots, battery warranty intelligence, and ODS-E schema validation.

## Installation

```bash
pip install asoba
```

Or from source:

```bash
git clone https://github.com/AsobaCloud/sdk.git
cd sdk/python
pip install -e .
```

## Quick start

```python
from asoba import OnaClient

client = OnaClient()

# Query historical inverter data
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

Set environment variables before running:

```bash
export INVERTER_TELEMETRY_ENDPOINT=https://telemetry.api.asoba.co
export OODA_TERMINAL_ENDPOINT=https://ooda.api.asoba.co
export PARTNER_API_ENDPOINT=https://partner.api.asoba.co
export INVERTER_TELEMETRY_API_KEY=<your_api_key>
export OODA_TERMINAL_API_KEY=<your_api_key>
export PARTNER_API_KEY=<your_api_key>
```

The same API key value works for all three variables.

## Inverter Telemetry

```python
from asoba import OnaClient

client = OnaClient()

# Historical data for one inverter
records = client.inverter_telemetry.get_inverter_telemetry(
    asset_id='INV-1000000054495190',
    site_id='Sibaya',
    time_range={'start': '2025-11-01T00:00:00', 'end': '2025-11-01T12:00:00'},
    resolution='5min',
    limit=100,
)

# Historical data for all inverters at a site
site_records = client.inverter_telemetry.get_site_telemetry(
    site_id='Sibaya',
    time_range={'start': '2025-11-01T00:00:00', 'end': '2025-11-01T12:00:00'},
)

# Discover available data range
period = client.inverter_telemetry.get_data_period(site_id='Sibaya')
print(f"Data from {period.first_record} to {period.last_record}")

# Stream live data (cursor-resumable)
for record in client.inverter_telemetry.stream_inverter(
    asset_id='INV-1000000054495190',
    site_id='Sibaya',
    polling_interval=30,
):
    print(f"{record.timestamp}: {record.power} kW")
```

## OODA Terminal Alerts

```python
from asoba.models.ooda import TimeRange

# Historical alerts for one terminal device
alerts = client.ooda_terminal.get_terminal_alerts(
    terminal_device_id='TERM-1000000054495190',
    site_id='Sibaya',
    time_range=TimeRange(start='2025-11-01T00:00:00', end='2025-11-01T12:00:00'),
    limit=100,
)

# All terminal devices at a site
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

## Partner API

Pre-computed snapshots with ETag caching — sub-100ms on repeat calls.

> `partner_api_endpoint` must use `https://` — `OnaConfig` raises `ConfigurationError` on init otherwise.

```python
# KPI rollup (first call: full fetch; second call: returns cached if ETag matches)
kpis = client.partner.get_kpi_rollup(site_id='Sibaya')
cached = client.partner.get_kpi_rollup(site_id='Sibaya')

# Maintenance signals (detected anomalies) — optional since/severity filters
signals = client.partner.get_maintenance_signals(
    site_id='Sibaya',
    since='2025-11-01T00:00:00',
    severity='high',
)

# 24h solar forecast snapshot
forecast = client.partner.get_forecast_snapshot(site_id='Sibaya')
print(f"{forecast['horizon_hours']}h, {len(forecast['intervals'])} intervals")

# 90-day preventive maintenance schedule (SEP-062)
schedule = client.partner.get_maintenance_schedule(site_id='Sibaya')
for task in schedule['tasks']:
    print(f"{task['recommended_date']} — {task['asset_id']} — {task['task_type']} ({task['priority']})")
```

## Battery & Site Intelligence

```python
# Site summary with battery health KPIs
summary = client.terminal.get_site_summary(site_id='Sibaya')
print(f"Fleet PR: {summary['fleet_pr_pct']}%")

if 'soiling' in summary:
    print(f"Soiling rate: {summary['soiling']['soiling_rate_pct_day']}%/day")

if 'battery' in summary:
    print(f"Avg SOH: {summary['battery']['avg_soh']}%")

# Asset detail (includes battery capacity and warranty)
asset = client.terminal.get_asset(customer_id='cust123', asset_id='BAT-001')

# Calculate remaining warranty life
status = client.terminal.calculate_remaining_warranty_life(
    warranty_expiry_date='2030-12-31',
    warranty_throughput_kwh=10000.0,
    current_throughput_kwh=8500.0,
)
print(f"{status['warranty_status']} — {status['throughput_remaining_pct']}% throughput remaining")
```

## ODS-E Data Validation

Validate records locally against the full 65-field energy-timeseries schema before uploading.

```python
from asoba.utils.validation import validate_batch, validate_with_profile

records = [
    {'timestamp': '2025-01-01T00:00:00Z', 'kWh': 100.5, 'error_type': 'normal'},
    {'timestamp': 'invalid-date', 'kWh': 'not-a-number', 'error_type': 'unknown'},
]

result = validate_batch(records)
print(f"Valid: {result['summary']['valid']}/{result['summary']['total']}")

for item in result['invalid_records']:
    print(f"Errors: {item['errors']}")
```

### Conformance profile validation

```python
# Bilateral trade settlement
is_valid, errors, normalized = validate_with_profile({
    'timestamp': '2026-06-27T14:00:00+02:00',
    'kWh': 87.3,
    'error_type': 'normal',
    'seller_party_id': 'nersa:gen:SOLARPK-001',
    'buyer_party_id': 'nersa:offtaker:MUN042',
    'settlement_period_start': '2026-06-27T14:00:00+02:00',
    'settlement_period_end': '2026-06-27T14:30:00+02:00',
    'contract_reference': 'PPA-SOLARPK-MUN042-2025-003',
    'settlement_type': 'bilateral',
}, 'bilateral')

# BESS dispatch
is_valid, errors, normalized = validate_with_profile({
    'timestamp': '2026-06-27T10:00:00Z',
    'kWh': 50.0,
    'error_type': 'normal',
    'dispatch_mode': 'charging',
    'soc': 75.0,
}, 'bess_dispatch')

# Wind SCADA
is_valid, errors, normalized = validate_with_profile({
    'timestamp': '2026-06-27T10:00:00Z',
    'kWh': 320.0,
    'error_type': 'normal',
    'wind_speed_ms': 8.5,
}, 'wind_scada')
```

Available profiles: `bilateral`, `wheeling`, `sawem_brp`, `municipal_recon`, `bess_dispatch`, `wind_scada`.

## Advanced ML Services

```python
# Trigger a training job
client.training.trigger_training(customer_id='Sibaya', promote=True)

# Check status
status = client.training.get_training_status(customer_id='Sibaya')
print(f"Training status: {status['status']}")

# Gap detection
result = client.gap_detection.detect_gaps(customer_id='Sibaya')
if result['needs_backfill']:
    print(f"Missing intervals: {result['total_missing_intervals']}")
```

## Error handling

```python
from asoba import OnaClient
from asoba.exceptions import ConfigurationError, ValidationError

try:
    records = client.inverter_telemetry.get_inverter_telemetry(...)
except ValidationError as e:
    print(f"Bad params: {e}")
except ConfigurationError as e:
    print(f"Config error: {e}")
```

## API reference

### Inverter Telemetry

| Method | Description |
|--------|-------------|
| `get_inverter_telemetry(...)` | Historical data for one inverter |
| `get_site_telemetry(...)` | Historical data for all inverters at a site |
| `get_data_period(...)` | Available data time range |
| `stream_inverter(...)` | Stream live data from one inverter |
| `stream_site(...)` | Stream live data from all inverters at a site |

### OODA Terminal Alerts

| Method | Description |
|--------|-------------|
| `get_terminal_alerts(...)` | Historical alerts for one terminal device |
| `get_site_alerts(...)` | Historical alerts for all terminal devices at a site |
| `get_asset(...)` | Asset details including battery capacity and warranty |
| `get_site_summary(...)` | Site summary with battery health KPIs |
| `get_data_period(...)` | Available alert time range |
| `stream_terminal(...)` | Stream live alerts from one terminal device |
| `stream_site(...)` | Stream live alerts from all terminal devices at a site |

### Partner API

| Method | Description |
|--------|-------------|
| `get_kpi_rollup(...)` | KPI summary snapshot (`KpiRollupSnapshot` with `EarKpis` + `FinancialKpis`) |
| `get_maintenance_signals(...)` | Pending maintenance and health signals |
| `get_forecast_snapshot(...)` | Pre-computed 24h solar forecast |
| `get_maintenance_schedule(...)` | 90-day preventive maintenance task list |
| `get_snapshot(...)` | Generic snapshot fetch by kind |

### Shared parameters

| Parameter | Description |
|-----------|-------------|
| `resolution` | `"5min"` (default) or `"daily"` |
| `limit` | Max records per query (default 100, max 1000) |
| `cursor` | Resume from a previous position |
| `polling_interval` | Seconds between polls when streaming (min 5, default 5) |

### Rate limits

- 60 requests per minute per API key
- Max 1000 records per query
- Max 31-day time range per query
- Min 5-second polling interval for streaming

## Migrating from `ona_platform`

The package was renamed from `ona_platform` to `asoba`. The old name still works during the migration window but emits a `DeprecationWarning`:

```python
# Before
from ona_platform import OnaClient   # DeprecationWarning

# After
from asoba import OnaClient
```

## Architecture

```
asoba/
├── client.py          — OnaClient
├── config.py          — OnaConfig dataclass
├── exceptions.py      — ConfigurationError, ValidationError, …
├── services/          — per-API clients
│   ├── inverter_telemetry.py
│   ├── ooda_terminal.py
│   ├── partner_api.py
│   ├── terminal.py
│   ├── training.py
│   └── …
├── models/            — typed dataclasses
│   ├── odse.py        — ODS-E schema constants and enums
│   ├── ooda.py        — TimeRange, alert models
│   ├── snapshots.py   — KpiRollupSnapshot, EarKpis, FinancialKpis
│   └── …
└── utils/
    ├── validation.py  — validate_batch, validate_with_profile
    └── …
ona_platform/          — deprecation shim (re-exports asoba)
```

## Requirements

- Python >= 3.8
- boto3 >= 1.28.0
- requests >= 2.31.0

## Examples

```bash
python3 examples/inverter_telemetry_example.py
python3 examples/ooda_terminal_example.py
python3 examples/partner_api_example.py
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT © [Asoba](https://asoba.co)
