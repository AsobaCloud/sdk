# Ona SDK

## What Works Right Now

This SDK currently provides **Inverter Telemetry Streaming** - query historical and stream live inverter data from solar installations. Other services are planned but not yet implemented.

**✅ Working Features:**
- Query historical inverter telemetry (5-minute and daily resolution)
- Stream live inverter data in real-time
- Resumable streaming with cursor tokens
- Built-in rate limiting and cost protection

**🚧 Planned Features:**
- Solar Energy Forecasting
- OODA Workflow (fault detection, diagnostics)
- Energy Policy Analysis
- Edge Device Management
- Data Collection integrations

---

## Quick Start

### 1. Get an API Key
Contact **support@asoba.co** to get an API key for inverter telemetry access.

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
pip install -e .
```

### 3. Set Environment Variables
```bash
export INVERTER_TELEMETRY_ENDPOINT=https://af5jy5ob3e.execute-api.af-south-1.amazonaws.com/prod
export INVERTER_TELEMETRY_API_KEY=<your_api_key_from_support>
```

### 4. Test It Works

**JavaScript:**
```bash
cd javascript
node examples/inverter-telemetry-example.js
```

**Python:**
```bash
cd python
python examples/inverter_telemetry_example.py
```

**Expected Output:**
```
=== Step 1: Discover available data period ===
Site data period:
  first_record: 2025-11-01T02:40:00
  last_record: 2025-11-29T23:55:00

=== Step 2: Historical Inverter Telemetry (5-min) ===
Retrieved 10 records
  2025-11-01T02:40:00  power=0.0 kW  temp=25.3°C  state=1  error=None
  ...
```

---

## Usage Examples

### Query Historical Data

**JavaScript:**
```javascript
const { OnaSDK } = require('./src/index');

const sdk = new OnaSDK({
  endpoints: {
    inverterTelemetry: process.env.INVERTER_TELEMETRY_ENDPOINT,
  },
  inverterTelemetryApiKey: process.env.INVERTER_TELEMETRY_API_KEY,
});

// Get historical data
const records = await sdk.inverterTelemetry.getInverterTelemetry({
  asset_id: 'INV-1000000054495190',
  site_id: 'Sibaya',
  time_range: { start: '2025-11-01T00:00:00', end: '2025-11-01T12:00:00' },
  resolution: '5min',
  limit: 100,
});

console.log(`Retrieved ${records.length} records`);
```

**Python:**
```python
from ona_platform import OnaClient

client = OnaClient()

# Get historical data
records = client.inverter_telemetry.get_inverter_telemetry(
    asset_id='INV-1000000054495190',
    site_id='Sibaya',
    time_range={'start': '2025-11-01T00:00:00', 'end': '2025-11-01T12:00:00'},
    resolution='5min',
    limit=100,
)

print(f"Retrieved {len(records)} records")
```

### Stream Live Data

**JavaScript:**
```javascript
// Stream live telemetry
for await (const record of sdk.inverterTelemetry.streamInverter({
  asset_id: 'INV-1000000054495190',
  site_id: 'Sibaya',
  polling_interval: 30, // seconds
})) {
  console.log(`${record.timestamp}: ${record.power} kW`);
}
```

**Python:**
```python
# Stream live telemetry
for record in client.inverter_telemetry.stream_inverter(
    asset_id='INV-1000000054495190',
    site_id='Sibaya',
    polling_interval=30,
):
    print(f"{record.timestamp}: {record.power} kW")
```

---

## API Reference

### Available Methods

**Query Methods:**
- `getInverterTelemetry()` - Get historical data for a single inverter
- `getSiteTelemetry()` - Get historical data for all inverters at a site
- `getDataPeriod()` - Discover available data time range

**Streaming Methods:**
- `streamInverter()` - Stream live data from a single inverter
- `streamSite()` - Stream live data from all inverters at a site

**Data Resolutions:**
- `5min` - 5-minute interval data (default)
- `daily` - Daily aggregated data

### Rate Limits
- **60 requests per minute** per API key
- **Max 1000 records** per query
- **Max 31-day time range** per query
- **Min 5-second polling interval** for streaming

---

## Troubleshooting

**Common Issues:**

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/missing API key | Check your API key with support@asoba.co |
| `403 Forbidden` | API key not scoped to site | Request access to the site_id you're querying |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry (60 req/min limit) |
| `ValidationError` | Invalid parameters | Check time ranges, limits, and required fields |

**Debug Steps:**
1. Verify environment variables are set: `echo $INVERTER_TELEMETRY_API_KEY`
2. Test with the provided examples first
3. Check the console output for detailed error messages
4. Ensure you're querying a valid site_id (try 'Sibaya' for testing)

---

## Development

### Repository Structure
```
sdk/
├── javascript/
│   ├── src/services/InverterTelemetryClient.js  # Core client
│   ├── examples/inverter-telemetry-example.js   # Working example
│   └── tests/                                   # Test suites
├── python/
│   ├── ona_platform/services/inverter_telemetry.py  # Core client
│   ├── examples/inverter_telemetry_example.py       # Working example
│   └── tests/                                       # Test suites
└── backend/                                         # Deployed Lambda backend
```

### Backend Infrastructure
- **Endpoint:** `https://af5jy5ob3e.execute-api.af-south-1.amazonaws.com/prod`
- **Region:** `af-south-1`
- **Authentication:** API key via `x-api-key` header
- **Data Source:** DynamoDB tables (`ona-platform-telemetry-5min`, `ona-platform-telemetry-daily`)

### For Contributors
1. Run the working examples to understand the API
2. Check existing tests in `tests/` directories
3. See individual SDK documentation:
   - [JavaScript SDK Details](./javascript/README.md)
   - [Python SDK Details](./python/README.md)

---

## Support

**Need an API Key?** Contact **support@asoba.co** with your use case.

**Issues?** 
- Check the troubleshooting section above
- Review the working examples in `examples/` directories
- Open an issue: https://github.com/AsobaCloud/sdk/issues

**Email:** support@asoba.co

---

## License

MIT License
