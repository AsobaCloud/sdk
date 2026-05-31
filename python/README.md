# Ona Platform SDK - Python

Python SDK for the Ona Energy Management Platform. Provides a unified interface to all platform services including solar forecasting, fault detection, AI diagnostics, energy policy analysis, and more.

## Features

- **Solar Energy Forecasting**: Device, site, and customer-level predictions
- **OODA Workflow**: Asset management, fault detection, diagnostics, and maintenance scheduling
- **Energy Policy Analysis**: RAG-powered queries on energy regulations
- **Edge Device Management**: Discovery, registration, and capability detection
- **Data Collection**: Enphase, Huawei, and weather data integration
- **ML Operations**: Model training, interpolation, and data standardization

## Installation

```bash
pip install ona-platform
```

Or install from source:

```bash
cd sdk/python
pip install -e .
```

## Quick Start

```python
from ona_platform import OnaClient

# Initialize client (uses environment variables)
client = OnaClient()

# Get solar forecast
forecast = client.forecasting.get_site_forecast('Sibaya', hours=24)
print(f"Next hour: {forecast['forecasts'][0]['kWh_forecast']} kWh")

# Run fault detection
detection = client.terminal.run_detection(
    customer_id='customer123',
    asset_id='asset456',
    lookback_hours=6
)
print(f"Severity: {detection['analysis']['severity_label']}")

# Query energy policies
answer = client.energy_analyst.query(
    "What are the grid code requirements for solar installations?"
)
print(answer['answer'])
```

## Configuration

Configure the SDK using environment variables or constructor parameters:

### Environment Variables

```bash
export AWS_REGION=af-south-1
export INPUT_BUCKET=sa-api-client-input
export OUTPUT_BUCKET=sa-api-client-output
export ENERGY_ANALYST_URL=http://localhost:8000
export EDGE_API_URL=http://localhost:8082
```

### Constructor Parameters

```python
client = OnaClient(
    aws_region='af-south-1',
    energy_analyst_url='http://localhost:8000',
    edge_api_url='http://localhost:8082',
    timeout=120,
    max_retries=3
)
```

## Services

### Forecasting API

Get solar energy forecasts at different levels:

```python
# Device-level forecast
device_forecast = client.forecasting.get_device_forecast(
    site_id='Sibaya',
    device_id='INV001',
    forecast_hours=24
)

# Site-level aggregated forecast
site_forecast = client.forecasting.get_site_forecast(
    site_id='Sibaya',
    forecast_hours=24,
    include_device_breakdown=True
)

# Customer-level forecast (legacy LSTM path)
# Pass platform customer_id (UUID) or legacy site-style id.
# forecastingApi maps UUID → site_name via ona-platform-customers, then loads
# customer_tailored/{site_name}/ or generic. Prefer get_site_forecast / get_device_forecast
# for site-based platform use. See services/forecastingApi/README.md.
customer_forecast = client.forecasting.get_customer_forecast(
    customer_id='customer123',
    forecast_hours=24
)
```

### Terminal API - OODA Workflow

Complete OODA (Observe, Orient, Decide, Act) workflow:

```python
# OBSERVE: Fault detection
detection = client.terminal.run_detection(
    customer_id='customer123',
    asset_id='asset456',
    lookback_hours=6
)

# ORIENT: AI diagnostics
diagnostic = client.terminal.run_diagnostics(
    customer_id='customer123',
    asset_id='asset456',
    detection_id=detection['detection_id']
)

# DECIDE: Create maintenance schedule
schedule = client.terminal.create_schedule(
    customer_id='customer123',
    asset_id='asset456',
    description='Replace inverter filter',
    priority='High',
    estimated_duration_hours=8
)

# ACT: View activity stream
activities = client.terminal.list_activities(
    customer_id='customer123'
)
```

#### Asset Management

```python
# List assets
assets = client.terminal.list_assets(customer_id='customer123')

# Add new asset
asset = client.terminal.add_asset(
    customer_id='customer123',
    asset_id='asset789',
    name='Solar Array 1',
    asset_type='solar',
    capacity_kw=150.0,
    location='Durban',
    timezone='Africa/Johannesburg'
)
```

#### ML Integration

```python
# Get forecast results
forecasts = client.terminal.get_forecast_results(
    customer_id='customer123'
)

# Get interpolation results
interpolations = client.terminal.get_interpolation_results(
    customer_id='customer123'
)

# Get model registry
models = client.terminal.get_ml_models()

# Get ML-enhanced OODA summaries
summaries = client.terminal.get_ml_ooda_summaries(
    customer_id='customer123'
)
```

#### Nowcast Data

```python
# Get real-time monitoring data
nowcast = client.terminal.get_nowcast_data(
    customer_id='customer123',
    time_range='1h',  # '1h', '6h', '24h', '7d', 'latest'
    asset_filter=['asset1', 'asset2']
)
```

#### Site Summary & Performance Intelligence

Get aggregated site-level KPIs including soiling analysis and asset prognostics:

```python
# Get high-level site summary
summary = client.terminal.get_site_summary(site_id='Sibaya')

print(f"Total kWh Today: {summary['total_kWh_today']}")
print(f"Fleet PR: {summary['fleet_pr_pct']}%")

# Soiling Audit
if summary.get('soiling'):
    soiling = summary['soiling']
    print(f"Soiling Rate: {soiling['soiling_rate_pct_day']}%/day")
    print(f"Recovery Gain: {soiling['recovery_gain_kwh_last_event']} kWh")

# Asset Prognostics
if summary.get('prognostics'):
    prog = summary['prognostics']
    print(f"Health Score: {prog['health_score']}/100")
    print(f"Battery Retirement: {prog['battery_retirement_date']}")
```

### Energy Analyst RAG

Query energy policies and regulations:

```python
# Query documents
result = client.energy_analyst.query(
    question="What are the NRS 097 grid connection requirements?",
    n_results=3,
    max_new_tokens=512,
    temperature=0.7
)
print(result['answer'])
print(f"Source: {result['citation']}")

# Upload PDF documents
upload_result = client.energy_analyst.upload_pdfs([
    '/path/to/policy1.pdf',
    '/path/to/policy2.pdf'
])

# Add text documents
client.energy_analyst.add_documents(
    texts=["Document text..."],
    metadatas=[{"source": "doc.pdf", "document_title": "Policy Document"}]
)

# Check service health
health = client.energy_analyst.health()
print(f"Documents: {health['document_count']}")

# Get collection info
info = client.energy_analyst.get_collection_info()
print(f"Storage: {info['storage_mb']} MB")
```

### Edge Device Registry

Discover and manage edge devices:

```python
# Discover new device
device = client.edge_devices.discover_device(
    ip='192.168.1.100',
    username='admin'
)

# List all devices
devices = client.edge_devices.list_devices()

# Get device details
details = client.edge_devices.get_device(device_id)

# Get device capabilities
capabilities = client.edge_devices.get_device_capabilities(device_id)

# Update device
client.edge_devices.update_device(
    device_id,
    {"name": "Updated Name", "status": "online"}
)
```

### Data Collection Services

#### Enphase

```python
# Collect real-time data
realtime = client.enphase.collect_realtime(site_id='site123')

# Collect historical data
historical = client.enphase.collect_historical(
    site_id='site123',
    start_date='2025-01-01',
    end_date='2025-01-31'
)
```

#### Huawei

```python
# Collect real-time data
realtime = client.huawei.collect_realtime(plant_code='plant456')

# Collect historical data
historical = client.huawei.collect_historical(
    plant_code='plant456',
    start_date='2025-01-01',
    end_date='2025-01-31'
)
```

#### Weather

```python
# Trigger weather update
client.weather.trigger_update()

# Get cached weather data
weather = client.weather.get_cached_weather(location='Durban')
```

### Data Processing Services

#### Interpolation

```python
result = client.interpolation.interpolate(
    customer_id='customer123',
    dataset_key='data/dataset.csv'
)
```

#### Standardization

```python
result = client.standardization.standardize(
    customer_id='customer123',
    dataset_key='data/dataset.csv'
)
```

#### Data Ingestion

```python
result = client.data_ingestion.ingest()
```

### ML Training

```python
# Start training job
job = client.training.start_training(
    model_type='forecasting',
    training_data_key='training/data.csv',
    model_params={'epochs': 100, 'batch_size': 32}
)

# Get training status
status = client.training.get_training_status(job_id='job123')

# List models
models = client.training.list_models()
```

## Error Handling

The SDK provides custom exceptions for different error types:

```python
from ona_platform import (
    OnaError,
    ConfigurationError,
    ServiceUnavailableError,
    ValidationError,
    ResourceNotFoundError,
    TimeoutError
)

try:
    result = client.forecasting.get_site_forecast('InvalidSite')
except ResourceNotFoundError as e:
    print(f"Site not found: {e}")
except ServiceUnavailableError as e:
    print(f"Service error: {e}")
except ValidationError as e:
    print(f"Invalid request: {e}")
except OnaError as e:
    print(f"SDK error: {e}")
```

## Retry Logic

The SDK automatically retries failed requests with exponential backoff:

- Max retries: 3 (configurable)
- Backoff factor: 2.0 (2s, 4s, 8s, 16s)
- Retries on: `ServiceUnavailableError`, `TimeoutError`

Configure retry behavior:

```python
client = OnaClient(max_retries=5, retry_backoff=2.5)
```

## Examples

See the `examples/` directory for complete usage examples:

- `forecasting_example.py` - Solar forecasting
- `terminal_ooda_example.py` - OODA workflow
- `energy_analyst_example.py` - Energy policy queries
- `edge_device_example.py` - Edge device management
- `complete_workflow_example.py` - Multi-service workflow

Run an example:

```bash
python examples/forecasting_example.py
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=ona_platform
```

### Code Formatting

```bash
black ona_platform/
flake8 ona_platform/
mypy ona_platform/
```

## Architecture

The SDK is organized into the following components:

- `client.py` - Main OnaClient class
- `config.py` - Configuration management
- `exceptions.py` - Custom exception classes
- `services/` - Service-specific clients
  - `base.py` - Base client with common functionality
  - `forecasting.py` - Forecasting API client
  - `terminal.py` - Terminal API client (OODA workflow)
  - `energy_analyst.py` - Energy Analyst RAG client
  - `edge_device.py` - Edge Device Registry client
  - `weather.py`, `enphase.py`, `huawei.py` - Data collection clients
  - `data_ingestion.py`, `interpolation.py`, `standardization.py` - Data processing
  - `training.py` - ML training client
- `utils/` - Utilities (retry, logging)
- `models/` - Data models (future expansion)

## Requirements

- Python >= 3.8
- boto3 >= 1.28.0
- requests >= 2.31.0

## AWS Credentials

The SDK uses boto3 for AWS services. Configure AWS credentials using:

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role (when running on EC2/Lambda)

See [boto3 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html) for details.

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:

- GitHub Issues: https://github.com/AsobaCloud/platform/issues
- Email: info@asoba.co

## Contributing

Contributions are welcome! Please follow the existing code style and include tests for new features.

## Changelog

### Version 1.0.0 (2025-01-29)

- Initial release
- Support for 11 platform services
- Comprehensive error handling and retry logic
- Complete documentation and examples
