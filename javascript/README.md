# <img src="https://raw.githubusercontent.com/AsobaCloud/sdk/main/docs/asoba-logo.svg" alt="Asoba" width="36" height="36" align="bottom" /> Ona SDK — JavaScript

[![npm](https://img.shields.io/npm/v/@asobacloud/sdk.svg)](https://www.npmjs.com/package/@asobacloud/sdk)
[![CI](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml/badge.svg)](https://github.com/AsobaCloud/sdk/actions/workflows/javascript-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

JavaScript SDK for live energy asset data — inverter telemetry, OODA terminal alerts, Partner API snapshots, and battery warranty intelligence.

## Installation

```bash
npm install @asobacloud/sdk
```

## Quick start

```javascript
const { OnaSDK } = require('@asobacloud/sdk');

const sdk = new OnaSDK();
// apiKey from ASOBA_API_KEY env var

// Query historical inverter data
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

Set environment variables before running:

```bash
export ASOBA_API_KEY=<your_api_key>
```

The same API key works for inverter telemetry, OODA terminal alerts, and the Partner API. Endpoint URLs are hardcoded to the canonical production values.

## Inverter Telemetry

```javascript
// Historical data for one inverter
const records = await sdk.inverterTelemetry.getInverterTelemetry({
  asset_id: 'INV-1000000054495190',
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
  resolution: '5min',   // '5min' | 'daily'
  limit: 100,
});

// Historical data for all inverters at a site
const siteRecords = await sdk.inverterTelemetry.getSiteTelemetry({
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
});

// Discover available data range
const period = await sdk.inverterTelemetry.getDataPeriod({ site_id: 'Sibaya' });
console.log(`Data from ${period.first_record} to ${period.last_record}`);

// Stream a single inverter (cursor-resumable)
for await (const record of sdk.inverterTelemetry.streamInverter({
  asset_id: 'INV-1000000054495190',
  site_id: 'Sibaya',
  polling_interval: 30,
})) {
  console.log(`${record.timestamp}: ${record.power} kW`);
}
```

## OODA Terminal Alerts

```javascript
// Historical alerts for one terminal device
const alerts = await sdk.oodaTerminal.getTerminalAlerts({
  terminal_device_id: 'TERM-1000000054495190',
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
  limit: 100,
});

// All terminal devices at a site
const siteAlerts = await sdk.oodaTerminal.getSiteAlerts({
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
});

// Stream live alerts
for await (const alert of sdk.oodaTerminal.streamTerminal({
  terminal_device_id: 'TERM-1000000054495190',
  site_id: 'Sibaya',
  polling_interval: 30,
})) {
  console.log(`${alert.timestamp}: [${alert.alert_severity}] ${alert.message}`);
}
```

## Partner API

Pre-computed snapshots with ETag caching — sub-100ms on repeat calls.

```javascript
// KPI rollup (typed KpiRollupSnapshot with EarKpis + FinancialKpis)
const kpis = await sdk.partner.getKpiRollup({ site_id: 'Sibaya' });
const cached = await sdk.partner.getKpiRollup({ site_id: 'Sibaya' }); // uses ETag

// Maintenance signals (detected anomalies)
const signals = await sdk.partner.getMaintenanceSignals({
  site_id: 'Sibaya',
  since: '2025-11-01T00:00:00',
  severity: 'high',
});

// 24h solar forecast snapshot
const forecast = await sdk.partner.getForecastSnapshot({ site_id: 'Sibaya' });
console.log(`${forecast.horizon_hours}h, ${forecast.intervals.length} intervals`);

// 90-day preventive maintenance schedule (SEP-062)
const schedule = await sdk.partner.getMaintenanceSchedule({ site_id: 'Sibaya' });
for (const task of schedule.tasks) {
  console.log(`${task.recommended_date} — ${task.asset_id} — ${task.task_type} (${task.priority})`);
}
```

## Battery & Site Intelligence

```javascript
// Site summary with battery health KPIs
const summary = await sdk.terminal.getSiteSummary({ site_id: 'Sibaya' });
console.log(`Fleet PR: ${summary.fleet_pr_pct}%`);

if (summary.soiling) {
  console.log(`Soiling rate: ${summary.soiling.soiling_rate_pct_day}%/day`);
}

// Asset detail (includes warranty fields for battery assets)
const asset = await sdk.terminal.getAsset({
  customer_id: 'cust123',
  asset_id: 'BAT-001',
});

// Calculate remaining warranty life
const status = sdk.terminal.constructor.calculateRemainingWarrantyLife({
  warranty_expiry_date: asset.warranty_expiry_date,
  warranty_throughput_kwh: asset.warranty_throughput_kwh,
  current_throughput_kwh: 5420.5,
});
console.log(`${status.warranty_status} — limited by ${status.limiting_factor}`);
```

## Advanced ML Services

```javascript
// Gap detection
const gaps = await sdk.gapDetection.detectGaps({ customer_id: 'Sibaya' });
if (gaps.needs_backfill) {
  console.log(`Missing intervals: ${gaps.total_missing_intervals}`);
}
```

## Error handling

```javascript
const { ConfigurationError, ValidationError, AuthenticationError } = require('@asobacloud/sdk');

try {
  const records = await sdk.inverterTelemetry.getInverterTelemetry({ ... });
} catch (err) {
  if (err instanceof ValidationError)     console.error('Bad params:', err.message);
  else if (err instanceof AuthenticationError) console.error('Auth failed:', err.message);
  else if (err instanceof ConfigurationError)  console.error('Config:', err.message);
  else throw err;
}
```

## API reference

### Inverter Telemetry

| Method | Description |
|--------|-------------|
| `getInverterTelemetry(params)` | Historical data for one inverter |
| `getSiteTelemetry(params)` | Historical data for all inverters at a site |
| `getDataPeriod(params)` | Available data time range |
| `streamInverter(params)` | Stream live data from one inverter |
| `streamSite(params)` | Stream live data from all inverters at a site |

### OODA Terminal Alerts

| Method | Description |
|--------|-------------|
| `getTerminalAlerts(params)` | Historical alerts for one terminal device |
| `getSiteAlerts(params)` | Historical alerts for all terminal devices at a site |
| `getAsset(params)` | Asset details including battery capacity and warranty |
| `getSiteSummary(params)` | Site summary with battery health KPIs |
| `getDataPeriod(params)` | Available alert time range |
| `streamTerminal(params)` | Stream live alerts from one terminal device |
| `streamSite(params)` | Stream live alerts from all terminal devices at a site |

### Partner API

| Method | Description |
|--------|-------------|
| `getKpiRollup(params)` | KPI summary snapshot (`KpiRollupSnapshot` with `EarKpis` + `FinancialKpis`) |
| `getMaintenanceSignals(params)` | Pending maintenance and health signals |
| `getForecastSnapshot(params)` | Pre-computed 24h solar forecast |
| `getMaintenanceSchedule(params)` | 90-day preventive maintenance task list |
| `getSnapshot(params)` | Generic snapshot fetch by kind |

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

## TypeScript

Type definitions are included. The `PartnerApiClient`, `KpiRollupSnapshot`, `EarKpis`, and `FinancialKpis` interfaces are exported from `src/types/index.d.ts`.

```typescript
import { OnaSDK, KpiRollupSnapshot, EarKpis } from '@asobacloud/sdk';

const sdk = new OnaSDK({ ... });
const kpis: KpiRollupSnapshot = await sdk.partner.getKpiRollup({ site_id: 'Sibaya' });
```

## Examples

```bash
node examples/inverter-telemetry-example.js
node examples/ooda-terminal-example.js
node examples/partner-api-example.js
```

## Development

```bash
git clone https://github.com/AsobaCloud/sdk.git
cd sdk/javascript
npm install
npm test
```

## License

MIT © [Asoba](https://asoba.co)
