"""Example usage of Edge Device Registry client."""

from ona_platform import OnaClient


def main():
    # Initialize client
    client = OnaClient(
        edge_api_url='http://localhost:8082'  # Or set EDGE_API_URL env var
    )

    # Example 1: Check service health
    print("=== Service Health ===")
    health = client.edge_devices.health()
    print(f"Service: {health['service']}")
    print(f"Status: {health['status']}")

    # Example 2: Discover a new device
    print("\n=== Discover New Device ===")
    device = client.edge_devices.discover_device(
        ip='192.168.1.100',
        username='admin'
    )
    print(f"Device ID: {device['id']}")
    print(f"Device Type: {device['type']}")
    print(f"Status: {device['status']}")
    print(f"Capabilities: {device['capabilities']}")

    # Example 3: List all devices
    print("\n=== List All Devices ===")
    devices = client.edge_devices.list_devices()
    print(f"Total devices: {len(devices)}")
    for dev in devices:
        print(f"  - {dev['name']} ({dev['ip']}): {dev['status']}")

    # Example 4: Get device details
    print("\n=== Get Device Details ===")
    device_id = device['id']
    details = client.edge_devices.get_device(device_id)
    print(f"Device: {details['name']}")
    print(f"Type: {details['type']}")
    print(f"Last Seen: {details['lastSeen']}")

    # Example 5: Get device capabilities
    print("\n=== Device Capabilities ===")
    capabilities = client.edge_devices.get_device_capabilities(device_id)
    print(f"System: {capabilities.get('system', {})}")
    print(f"Docker: {capabilities.get('docker', {})}")
    print(f"Services: {capabilities.get('services', [])}")

    # Example 6: Update device
    print("\n=== Update Device ===")
    updated = client.edge_devices.update_device(
        device_id,
        {"name": "Updated Edge Device", "status": "online"}
    )
    print(f"Updated device: {updated['name']}")

    # Example 7: Delete device (commented out for safety)
    # print("\n=== Delete Device ===")
    # result = client.edge_devices.delete_device(device_id)
    # print(f"Delete result: {result['message']}")


if __name__ == '__main__':
    main()
