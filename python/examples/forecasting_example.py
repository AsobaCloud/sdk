"""Example usage of Forecasting API client."""

from ona_platform import OnaClient


def main():
    # Initialize client
    client = OnaClient()

    # Example 1: Get device-level forecast
    print("=== Device-Level Forecast ===")
    device_forecast = client.forecasting.get_device_forecast(
        site_id='Sibaya',
        device_id='INV001',
        forecast_hours=24
    )
    print(f"Site: {device_forecast['site_id']}")
    print(f"Device: {device_forecast['device_id']}")
    print(f"Forecast hours: {len(device_forecast['forecasts'])}")
    print(f"First forecast: {device_forecast['forecasts'][0]}")

    # Example 2: Get site-level aggregated forecast
    print("\n=== Site-Level Aggregated Forecast ===")
    site_forecast = client.forecasting.get_site_forecast(
        site_id='Sibaya',
        forecast_hours=24,
        include_device_breakdown=True
    )
    print(f"Site: {site_forecast['site_id']}")
    print(f"Devices included: {site_forecast['devices_included']}")
    print(f"Total forecast hours: {len(site_forecast['forecasts'])}")
    print(f"First hour total kWh: {site_forecast['forecasts'][0]['kWh_forecast']}")

    # Example 3: Get customer-level forecast (legacy)
    print("\n=== Customer-Level Forecast ===")
    customer_forecast = client.forecasting.get_customer_forecast(
        customer_id='customer123',
        forecast_hours=24
    )
    print(f"Customer: {customer_forecast['customer_id']}")
    print(f"Model info: {customer_forecast['model_info']}")


if __name__ == '__main__':
    main()
