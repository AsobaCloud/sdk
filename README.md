# Ona SDK

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python CI](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/python-ci.yml)
[![JavaScript CI](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml)

## What Works Right Now

This SDK provides three live APIs for solar installation data:

**✅ Working Features:**
- **Inverter Telemetry** — query historical and stream live inverter data (5-min and daily resolution)
- **OODA Terminal Alerts** — query historical and stream live OODA fault/diagnostic alerts from terminal devices
- **Partner API** — fetch pre-computed JSON snapshots (KPIs, maintenance signals, forecasts, and preventive-maintenance schedules) with sub-100ms response times via ETag caching
- Resumable streaming with cursor tokens for telemetry and alerts
- Built-in rate limiting and cost protection

**🚧 Planned Features:**
- Solar Energy Forecasting (Working)
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
const kpis = await sdk.partnerApi.getKpiRollup({ site_id: 'Sibaya' });
const cachedKpis = await sdk.partnerApi.getKpiRollup({ site_id: 'Sibaya' });

// 2. Maintenance signals (detected anomalies) — optional `since` and `severity` filters
const signals = await sdk.partnerApi.getMaintenanceSignals({
  site_id: 'Sibaya',
  since: '2025-11-01T00:00:00',
  severity: 'high',
});

// 3. Forecast snapshot — pre-computed 24h solar forecast (optional `horizon`)
const forecast = await sdk.partnerApi.getForecastSnapshot({ site_id: 'Sibaya' });
console.log(`Forecast horizon: ${forecast.horizon_hours}h, intervals: ${forecast.intervals.length}`);

// 4. Maintenance schedule (90-day preventive tasks) — SEP-062
const schedule = await sdk.partnerApi.getMaintenanceSchedule({ site_id: 'Sibaya' });
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
kpis = client.partner_api.get_kpi_rollup(site_id='Sibaya')
cached_kpis = client.partner_api.get_kpi_rollup(site_id='Sibaya')

# 2. Maintenance signals (detected anomalies) — optional `since` and `severity` filters
signals = client.partner_api.get_maintenance_signals(
    site_id='Sibaya',
    since='2025-11-01T00:00:00',
    severity='high',
)

# 3. Forecast snapshot — pre-computed 24h solar forecast (optional `horizon`)
forecast = client.partner_api.get_forecast_snapshot(site_id='Sibaya')
print(f"Forecast horizon: {forecast['horizon_hours']}h, intervals: {len(forecast['intervals'])}")

# 4. Maintenance schedule (90-day preventive tasks) — SEP-062
schedule = client.partner_api.get_maintenance_schedule(site_id='Sibaya')
print(f"Tasks: {schedule['summary']['total_tasks']}")
for task in schedule['tasks']:
    print(f"  {task['recommended_date']} — {task['asset_id']} — {task['task_type']} ({task['priority']})")
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

### OODA Terminal Alert Methods
| Method | Description |
|--------|-------------|
| `getTerminalAlerts` / `get_terminal_alerts` | Historical alerts for a single terminal device |
| `getSiteAlerts` / `get_site_alerts` | Historical alerts for all terminal devices at a site |
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
| `getKpiRollup` / `get_kpi_rollup` | Site-level KPI summary snapshot |
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
│   ├── examples/inverter_telemetry_example.py
│   ├── examples/ooda_terminal_example.py
│   ├── examples/partner_api_example.py
│   └── tests/
│       ├── test_client.py
│       ├── test_inverter_telemetry_client.py
│       └── test_partner_api_client.py
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
