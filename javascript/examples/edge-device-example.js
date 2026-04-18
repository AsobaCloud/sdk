/**
 * Edge Device Registry Example
 * Demonstrates edge device discovery, registration, and management
 */

const { OnaSDK } = require('../src/index');

async function main() {
  const sdk = new OnaSDK({
    region: 'af-south-1',
    endpoints: {
      edgeRegistry: process.env.ONA_EDGE_REGISTRY_ENDPOINT || 'http://edge-registry:8082'
    }
  });

  try {
    // Check service health
    console.log('=== Service Health Check ===\n');
    const health = await sdk.edgeRegistry.getHealth();
    console.log(`Service: ${health.service}`);
    console.log(`Status: ${health.status}`);
    console.log(`Version: ${health.version}`);

    // Get all registered devices
    console.log('\n=== Registered Devices ===\n');
    const devices = await sdk.edgeRegistry.getDevices();
    console.log(`Total devices: ${devices.length}`);

    if (devices.length > 0) {
      devices.forEach(device => {
        console.log(`\nDevice: ${device.name} (${device.id})`);
        console.log(`  IP: ${device.ip}`);
        console.log(`  Type: ${device.type}`);
        console.log(`  Status: ${device.status}`);
        console.log(`  Last seen: ${device.lastSeen}`);
      });
    }

    // Discover a new device (example - adjust IP and username)
    const shouldDiscoverNewDevice = false; // Set to true to discover
    if (shouldDiscoverNewDevice) {
      console.log('\n=== Device Discovery ===\n');

      const newDevice = await sdk.edgeRegistry.discoverDevice({
        ip: '192.168.1.100',
        username: 'admin'
      });

      console.log(`✓ Device discovered: ${newDevice.id}`);
      console.log(`  Name: ${newDevice.name}`);
      console.log(`  Type: ${newDevice.type}`);
      console.log(`  Status: ${newDevice.status}`);

      // Get device capabilities
      console.log('\n=== Device Capabilities ===\n');
      const capabilities = await sdk.edgeRegistry.getDeviceCapabilities(newDevice.id);

      console.log('System capabilities:');
      console.log(JSON.stringify(capabilities.system, null, 2));

      if (capabilities.docker) {
        console.log('\nDocker:');
        console.log(`  Installed: ${capabilities.docker.installed}`);
        console.log(`  Version: ${capabilities.docker.version || 'N/A'}`);
      }

      if (capabilities.platformEdge) {
        console.log('\nPlatform Edge:');
        console.log(`  Deployed: ${capabilities.platformEdge.deployed}`);
        console.log(`  Version: ${capabilities.platformEdge.version || 'N/A'}`);
      }

      // Get device services
      console.log('\n=== Device Services ===\n');
      const services = await sdk.edgeRegistry.getDeviceServices(newDevice.id);

      if (services.length > 0) {
        services.forEach(service => {
          console.log(`  - ${service.name} (${service.status}) on port ${service.port}`);
        });
      } else {
        console.log('  No services detected');
      }

      // Update device information
      console.log('\n=== Update Device ===\n');
      const updated = await sdk.edgeRegistry.updateDevice(newDevice.id, {
        name: 'Updated Edge Device Name'
      });
      console.log(`✓ Device updated: ${updated.name}`);
    }

    // Get detailed information about first device
    if (devices.length > 0) {
      const firstDevice = devices[0];

      console.log('\n=== Detailed Device Information ===\n');
      const deviceDetails = await sdk.edgeRegistry.getDevice(firstDevice.id);

      console.log(`Device ID: ${deviceDetails.id}`);
      console.log(`Name: ${deviceDetails.name}`);
      console.log(`IP: ${deviceDetails.ip}`);
      console.log(`Type: ${deviceDetails.type}`);
      console.log(`Status: ${deviceDetails.status}`);
      console.log(`Created: ${deviceDetails.createdAt}`);
      console.log(`Last seen: ${deviceDetails.lastSeen}`);

      console.log('\nCapabilities:');
      console.log(JSON.stringify(deviceDetails.capabilities, null, 2));

      // Get device capabilities
      const capabilities = await sdk.edgeRegistry.getDeviceCapabilities(firstDevice.id);

      console.log('\n=== System Status ===');
      if (capabilities.system && capabilities.system.available) {
        console.log(`✓ System available`);
        console.log(`  Service: ${capabilities.system.service}`);
        console.log(`  Version: ${capabilities.system.version}`);
      } else {
        console.log('✗ System not available');
      }

      // Get running services
      const services = await sdk.edgeRegistry.getDeviceServices(firstDevice.id);
      console.log(`\nRunning services: ${services.length}`);
      services.forEach(service => {
        console.log(`  ✓ ${service.name} on port ${service.port}`);
      });
    }

    // Example: Delete a device (commented out for safety)
    // const shouldDelete = false;
    // if (shouldDelete && devices.length > 0) {
    //   console.log('\n=== Delete Device ===\n');
    //   const deviceToDelete = devices[0].id;
    //   await sdk.edgeRegistry.deleteDevice(deviceToDelete);
    //   console.log(`✓ Device deleted: ${deviceToDelete}`);
    // }

  } catch (error) {
    console.error('Error:', error.message);
    if (error.statusCode) {
      console.error('HTTP status:', error.statusCode);
    }
    if (error.response) {
      console.error('Response:', error.response);
    }
  }
}

main().catch(console.error);
