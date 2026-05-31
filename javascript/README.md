# Asoba Ona Energy Management Platform - JavaScript SDK

Official JavaScript SDK for the Asoba Ona Energy Management Platform. This SDK provides a comprehensive interface to all Ona platform services including forecasting, OODA workflow management, edge device registry, energy policy analysis, and more.

## Features

- ✅ **Complete Service Coverage** - Access all 13 Ona platform services
- ✅ **TypeScript Support** - Full TypeScript type definitions included
- ✅ **Modern JavaScript** - ES6+ syntax with Promise-based API
- ✅ **Automatic Retries** - Built-in retry logic for failed requests
- ✅ **AWS Integration** - AWS Signature v4 signing for Lambda services
- ✅ **Comprehensive Error Handling** - Custom error classes with detailed messages
- ✅ **Input Validation** - Built-in validation for all API calls
- ✅ **Well Documented** - JSDoc comments and examples for every method

## Installation

```bash
npm install @asoba/ona-sdk
```

## Quick Start

```javascript
const { OnaSDK } = require('@asoba/ona-sdk');

// Initialize the SDK
const sdk = new OnaSDK({
  region: 'af-south-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  },
  endpoints: {
    forecasting: 'https://forecasting.api.asoba.co',
    terminal: 'https://terminal.api.asoba.co',
    edgeRegistry: 'http://edge-registry:8082',
    energyAnalyst: 'http://energy-analyst:8000'
  }
});

// Get energy forecast
const forecast = await sdk.forecasting.getSiteForecast({
  site_id: 'Sibaya',
  forecast_hours: 24
});

console.log('Forecast:', forecast);
```

## Services

### Forecasting API

Generate energy forecasts at device, site, or customer levels.

```javascript
// Device-level forecast
const deviceForecast = await sdk.forecasting.getDeviceForecast({
  site_id: 'Sibaya',
  device_id: 'INV001',
  forecast_hours: 24
});

// Site-level forecast (aggregated)
const siteForecast = await sdk.forecasting.getSiteForecast({
  site_id: 'Sibaya',
  forecast_hours: 24,
  include_device_breakdown: true
});

// Customer-level forecast (legacy)
const customerForecast = await sdk.forecasting.getCustomerForecast({
  customer_id: 'customer123',
  forecast_hours: 24
});
```

### Terminal API (OODA Workflow)

Comprehensive API for Observe, Orient, Decide, Act workflow operations.

```javascript
// List all assets
const assets = await sdk.terminal.listAssets({
  customer_id: 'customer123'
});

// Run fault detection (Observe)
const detection = await sdk.terminal.runDetection({
  customer_id: 'customer123',
  asset_id: 'asset456',
  lookback_hours: 6
});

// Run diagnostics (Orient)
const diagnostic = await sdk.terminal.runDiagnostics({
  customer_id: 'customer123',
  asset_id: 'asset456',
  detection_id: detection.detection_id
});

// Create maintenance schedule (Decide)
const schedule = await sdk.terminal.createSchedule({
  customer_id: 'customer123',
  asset_id: 'asset456',
  priority: 'High',
  description: 'Replace faulty inverter'
});

// Get real-time monitoring data
const nowcast = await sdk.terminal.getNowcastData({
  customer_id: 'customer123',
  time_range: '1h'
});

// Get high-level site summary with intelligence data
const summary = await sdk.terminal.getSiteSummary({
  site_id: 'Sibaya'
});

console.log(`Site PR: ${summary.fleet_pr_pct}%`);

if (summary.soiling) {
  console.log(`Soiling Rate: ${summary.soiling.soiling_rate_pct_day}%/day`);
}

if (summary.prognostics) {
  console.log(`Asset Health: ${summary.prognostics.health_score}/100`);
}
```

### Energy Analyst (RAG)

AI-powered energy policy and regulatory compliance analysis.

```javascript
// Query the RAG system
const answer = await sdk.energyAnalyst.query({
  question: 'What are the key regulatory requirements for solar installations in South Africa?',
  n_results: 3,
  temperature: 0.7
});

console.log('Answer:', answer.answer);
console.log('Citation:', answer.citation);

// Add documents to the knowledge base
await sdk.energyAnalyst.addDocuments({
  texts: [
    'Document text 1...',
    'Document text 2...'
  ],
  metadatas: [
    { source: 'regulation.pdf', page: 1 },
    { source: 'regulation.pdf', page: 2 }
  ]
});

// Get collection information
const info = await sdk.energyAnalyst.getCollectionInfo();
console.log(`Collection has ${info.count} documents (${info.storage_mb} MB)`);
```

### Edge Device Registry

Manage distributed edge devices with automatic capability detection.

```javascript
// Get all devices
const devices = await sdk.edgeRegistry.getDevices();

// Discover and register a new device
const device = await sdk.edgeRegistry.discoverDevice({
  ip: '192.168.1.100',
  username: 'admin'
});

// Get device capabilities
const capabilities = await sdk.edgeRegistry.getDeviceCapabilities(device.id);

// Get device services
const services = await sdk.edgeRegistry.getDeviceServices(device.id);
```

### Enphase & Huawei Clients

Access inverter data from Enphase and Huawei systems.

```javascript
// Enphase data
const enphaseHistorical = await sdk.enphase.getHistoricalData({
  site_id: 'site123',
  start_date: '2025-01-01',
  end_date: '2025-01-31'
});

const enphaseRealtime = await sdk.enphase.getRealTimeData({
  site_id: 'site123'
});

// Huawei data
const huaweiHistorical = await sdk.huawei.getHistoricalData({
  site_id: 'site123',
  start_date: '2025-01-01',
  end_date: '2025-01-31'
});

const huaweiRealtime = await sdk.huawei.getRealTimeData({
  site_id: 'site123'
});
```

## Configuration

### SDK Options

```javascript
const sdk = new OnaSDK({
  // AWS region (default: 'af-south-1')
  region: 'af-south-1',

  // AWS credentials for Lambda services
  credentials: {
    accessKeyId: 'YOUR_ACCESS_KEY',
    secretAccessKey: 'YOUR_SECRET_KEY',
    sessionToken: 'OPTIONAL_SESSION_TOKEN'
  },

  // Service endpoints
  endpoints: {
    forecasting: 'https://forecasting.api.asoba.co',
    terminal: 'https://terminal.api.asoba.co',
    edgeRegistry: 'http://edge-registry:8082',
    energyAnalyst: 'http://energy-analyst:8000',
    // ... other endpoints
  },

  // Request timeout in milliseconds (default: 30000)
  timeout: 30000,

  // Number of retries for failed requests (default: 3)
  retries: 3,

  // Delay between retries in milliseconds (default: 1000)
  retryDelay: 1000
});
```

### Environment Variables

You can also configure the SDK using environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=af-south-1
export ONA_FORECASTING_ENDPOINT=https://forecasting.api.asoba.co
export ONA_TERMINAL_ENDPOINT=https://terminal.api.asoba.co
```

## Error Handling

The SDK provides custom error classes for different error scenarios:

```javascript
const {
  OnaSDKError,
  APIError,
  ConfigurationError,
  ValidationError,
  AuthenticationError,
  TimeoutError
} = require('@asoba/ona-sdk');

try {
  const forecast = await sdk.forecasting.getSiteForecast({
    site_id: 'Sibaya',
    forecast_hours: 24
  });
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Validation error:', error.field, error.message);
  } else if (error instanceof APIError) {
    console.error('API error:', error.statusCode, error.message);
  } else if (error instanceof TimeoutError) {
    console.error('Request timed out after', error.timeout, 'ms');
  } else if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message);
  } else {
    console.error('Unknown error:', error);
  }
}
```

## TypeScript Support

The SDK includes comprehensive TypeScript type definitions:

```typescript
import { OnaSDK, SiteForecastParams, ForecastResult } from '@asoba/ona-sdk';

const sdk = new OnaSDK({
  region: 'af-south-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
  }
});

const params: SiteForecastParams = {
  site_id: 'Sibaya',
  forecast_hours: 24
};

const result: ForecastResult = await sdk.forecasting.getSiteForecast(params);
```

## Examples

See the `examples/` directory for complete working examples:

- `basic-usage.js` - Basic SDK initialization and usage
- `forecasting-example.js` - Energy forecasting examples
- `terminal-api-example.js` - OODA workflow examples
- `edge-device-example.js` - Edge device management examples

## API Reference

### Forecasting Client

- `getDeviceForecast(params)` - Get device-level forecast
- `getSiteForecast(params)` - Get site-level forecast (aggregated)
- `getCustomerForecast(params)` - Get customer-level forecast (legacy)

### Terminal Client

**Assets:**
- `listAssets(params)` - List all assets
- `addAsset(params)` - Add a new asset
- `getAsset(params)` - Get specific asset

**Detection (Observe):**
- `runDetection(params)` - Run fault detection
- `listDetections(params)` - List detections

**Diagnostics (Orient):**
- `runDiagnostics(params)` - Run diagnostics
- `listDiagnostics(params)` - List diagnostics

**Scheduling (Decide):**
- `createSchedule(params)` - Create maintenance schedule
- `listSchedules(params)` - List schedules

**Operations (Act):**
- `buildBOM(params)` - Build Bill of Materials
- `listBOMs(params)` - List BOMs
- `createOrder(params)` - Create work order
- `listOrders(params)` - List orders

**Monitoring:**
- `getNowcastData(params)` - Get real-time monitoring data
- `listActivities(params)` - List all OODA activities
- `listIssues(params)` - List issues

**ML Integration:**
- `getForecastResults(params)` - Get ML forecast results
- `getInterpolationResults(params)` - Get interpolation results
- `getMLModels()` - Get ML model registry
- `getMLOODA(params)` - Get ML-enhanced OODA data

### Energy Analyst Client

- `query(params)` - Query the RAG system
- `addDocuments(params)` - Add documents to knowledge base
- `uploadPDFs(files)` - Upload PDF files
- `getCollectionInfo()` - Get collection information
- `clearCollection()` - Clear all documents
- `getHealth()` - Get service health

### Edge Device Registry Client

- `getDevices()` - Get all devices
- `getDevice(deviceId)` - Get specific device
- `discoverDevice(params)` - Discover and register device
- `updateDevice(deviceId, updates)` - Update device
- `deleteDevice(deviceId)` - Delete device
- `getDeviceCapabilities(deviceId)` - Get device capabilities
- `getDeviceServices(deviceId)` - Get device services
- `getHealth()` - Get service health

## License

MIT

## Support

For issues and questions:
- GitHub Issues: https://github.com/AsobaCloud/platform/issues
- Documentation: https://docs.asoba.co

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.
