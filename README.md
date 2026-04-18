# Ona SDK

## Introduction

The **Ona SDK** provides seamless integration with the **Ona Energy AI Platform**, enabling developers to build applications that interact with Asoba's energy management services. This SDK supports both **JavaScript (Node.js & Browser)** and **Python**, making it easy to integrate Ona into third-party applications.

### Key Features

✔ **Solar Energy Forecasting** – Device, site, and customer-level predictions  
✔ **Inverter Telemetry Streaming** – Real-time and historical inverter data via API key-authenticated backend  
✔ **OODA Workflow** – Asset management, fault detection, diagnostics, and maintenance scheduling  
✔ **Energy Policy Analysis** – RAG-powered queries on energy regulations  
✔ **Edge Device Management** – Discovery, registration, and capability detection  
✔ **Data Collection** – Enphase, Huawei, and weather data integration  
✔ **ML Operations** – Model training, interpolation, and data standardization  
✔ **Dual SDK Support** – Use in both **JavaScript** and **Python** applications  
✔ **Comprehensive Error Handling** – Detailed API responses and logging for debugging  

---

## SDKs

This repository contains two SDK implementations:

### JavaScript SDK
Official JavaScript/TypeScript SDK for Node.js and browser environments.

**📖 [View JavaScript SDK Documentation →](./javascript/README.md)**

**Quick Start:**
```javascript
const { OnaSDK } = require('@asoba/ona-sdk');

const sdk = new OnaSDK({
  region: 'af-south-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});

// Get energy forecast
const forecast = await sdk.forecasting.getSiteForecast({
  site_id: 'Sibaya',
  forecast_hours: 24
});

// Stream live inverter telemetry
for await (const record of sdk.inverterTelemetry.streamInverter({
  asset_id: 'INV-1000000054495190',
  site_id: 'Sibaya',
})) {
  console.log(`${record.timestamp}: ${record.power} kW`);
}
```

### Python SDK
Official Python SDK for server-side and data science applications.

**📖 [View Python SDK Documentation →](./python/README.md)**

**Quick Start:**
```python
from ona_platform import OnaClient

client = OnaClient()

# Get solar forecast
forecast = client.forecasting.get_site_forecast('Sibaya', hours=24)

# Run fault detection
detection = client.terminal.run_detection(
    customer_id='customer123',
    asset_id='asset456',
    lookback_hours=6
)

# Stream live inverter telemetry
for record in client.inverter_telemetry.stream_inverter(
    asset_id='INV-1000000054495190',
    site_id='Sibaya',
):
    print(f"{record.timestamp}: {record.power} kW")
```

---

## Installation

### JavaScript SDK

```bash
# Install from source (development)
cd javascript
npm install
```

For detailed installation and setup instructions, see the [JavaScript SDK Documentation](./javascript/README.md).

### Python SDK

```bash
# Install from source (development)
cd python
pip install -e .
```

For detailed installation and setup instructions, see the [Python SDK Documentation](./python/README.md).

---

## Configuration

Both SDKs support configuration via environment variables or constructor parameters.

### Environment Variables

```bash
# AWS Configuration
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=af-south-1

# Service Endpoints (optional)
export ONA_FORECASTING_ENDPOINT=https://forecasting.api.asoba.co
export ONA_TERMINAL_ENDPOINT=https://terminal.api.asoba.co

# Inverter Telemetry (required for telemetry features)
export INVERTER_TELEMETRY_ENDPOINT=https://your-telemetry-api.execute-api.af-south-1.amazonaws.com/prod
export INVERTER_TELEMETRY_API_KEY=your_api_key
```

See the individual SDK documentation for complete configuration options:
- [JavaScript SDK Configuration](./javascript/README.md#configuration)
- [Python SDK Configuration](./python/README.md#configuration)

---

## Services

The Ona SDK provides access to the following platform services:

### Forecasting API
Generate energy forecasts at device, site, or customer levels.

### Terminal API (OODA Workflow)
Comprehensive API for Observe, Orient, Decide, Act workflow operations including:
- Asset management
- Fault detection
- AI diagnostics
- Maintenance scheduling
- Real-time monitoring

### Energy Analyst (RAG)
AI-powered energy policy and regulatory compliance analysis.

### Edge Device Registry
Manage distributed edge devices with automatic capability detection.

### Data Collection
Integration with Enphase, Huawei, and weather data services.

### ML Operations
Model training, interpolation, and data standardization services.

### Inverter Telemetry Streaming
Query historical and stream live inverter telemetry data from DynamoDB-backed storage. Access is gated by API key — no AWS credentials required in the SDK. Each API key is scoped to one or more permitted sites.

- Query 5-minute or daily resolution historical data for a single inverter or all inverters at a site
- Stream live telemetry with configurable polling interval (minimum 5 seconds)
- Resumable streams via cursor tokens
- Built-in cost protection: max 1000 records per query, max 31-day time range

For detailed API documentation, see:
- [JavaScript SDK API Reference](./javascript/README.md#api-reference)
- [Python SDK API Reference](./python/README.md#examples)

---

## Examples

Both SDKs include comprehensive examples:

### JavaScript Examples
Located in `javascript/examples/`:
- `basic-usage.js` – Basic SDK initialization and usage
- `forecasting-example.js` – Energy forecasting examples
- `terminal-api-example.js` – OODA workflow examples
- `edge-device-example.js` – Edge device management examples
- `inverter-telemetry-example.js` – Inverter telemetry queries and live streaming

### Python Examples
Located in `python/examples/`:
- `forecasting_example.py` – Solar forecasting
- `terminal_ooda_example.py` – OODA workflow
- `energy_analyst_example.py` – Energy policy queries
- `edge_device_example.py` – Edge device management
- `inverter_telemetry_example.py` – Inverter telemetry queries and live streaming
- `complete_workflow_example.py` – Multi-service workflow

---

## Error Handling

Both SDKs provide comprehensive error handling with custom error classes:

### JavaScript
```javascript
const {
  OnaSDKError,
  APIError,
  ValidationError,
  AuthenticationError,
  TimeoutError,
  RateLimitError,
  ServiceUnavailableError
} = require('@asoba/ona-sdk');
```

### Python
```python
from ona_platform import (
    OnaError,
    ConfigurationError,
    ServiceUnavailableError,
    ValidationError,
    ResourceNotFoundError,
    TimeoutError
)
from ona_platform.services.inverter_telemetry import RateLimitError
```

See the individual SDK documentation for detailed error handling examples.

---

## Troubleshooting

**403 Forbidden?** Ensure your API key is valid and scoped to the requested `site_id`.  
**401 Unauthorized?** Your API key may be missing, expired, or revoked.  
**429 Too Many Requests?** You've exceeded the rate limit (60 req/min). Back off and retry.  
**SignatureDoesNotMatch?** Verify your AWS credentials and region settings.  
**Connection Timeout?** Check your internet connection and retry.  
**Service Unavailable?** Verify service endpoints are correct and accessible.

For more troubleshooting help, see:
- [JavaScript SDK Documentation](./javascript/README.md)
- [Python SDK Documentation](./python/README.md)

---

## Support

For support, reach out to:
- **Email:** support@asoba.co
- **GitHub Issues:** https://github.com/AsobaCloud/platform/issues
- **Documentation:** https://docs.asoba.co

---

## License

MIT License

---

## Contributing

Contributions are welcome! Please see the individual SDK documentation for contribution guidelines:
- [JavaScript SDK Contributing](./javascript/README.md#contributing)
- [Python SDK Contributing](./python/README.md#contributing)
