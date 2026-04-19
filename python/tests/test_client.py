"""Basic tests for OnaClient."""

from ona_platform import OnaClient, OnaConfig


def test_client_initialization():
    """Test client can be initialized."""
    client = OnaClient(aws_region="af-south-1")
    assert client.config.aws_region == "af-south-1"


def test_client_from_config():
    """Test client initialization from config object."""
    config = OnaConfig(aws_region="us-east-1")
    client = OnaClient(config=config)
    assert client.config.aws_region == "us-east-1"


def test_lazy_service_loading():
    """Test that services are lazy-loaded."""
    client = OnaClient()
    assert client._forecasting is None

    # Access forecasting service
    _ = client.forecasting
    assert client._forecasting is not None


def test_config_from_env(monkeypatch):
    """Test configuration from environment variables."""
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("INPUT_BUCKET", "test-input")
    monkeypatch.setenv("OUTPUT_BUCKET", "test-output")

    config = OnaConfig.from_env()
    assert config.aws_region == "eu-west-1"
    assert config.input_bucket == "test-input"
    assert config.output_bucket == "test-output"
