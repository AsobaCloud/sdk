#!/usr/bin/env node
/**
 * OODA Terminal API Example
 * 
 * This example demonstrates how to use the OODA Terminal API to query and stream
 * OODA (Observe, Orient, Decide, Act) alerts from terminal devices.
 * 
 * Requirements:
 * - Set OODA_TERMINAL_ENDPOINT environment variable
 * - Set OODA_TERMINAL_API_KEY environment variable
 * 
 * Example usage:
 *   export OODA_TERMINAL_ENDPOINT="https://your-ooda-api.execute-api.af-south-1.amazonaws.com/prod"
 *   export OODA_TERMINAL_API_KEY="your-api-key-here"
 *   node ooda-terminal-example.js
 */

const { OnaSDK } = require('../src/index');

async function main() {
  console.log('🔗 OODA Terminal API Example');
  
  // Initialize the SDK
  const sdk = new OnaSDK({
    endpoints: {
      oodaTerminal: process.env.OODA_TERMINAL_ENDPOINT
    },
    oodaTerminalApiKey: process.env.OODA_TERMINAL_API_KEY
  });
  
  // Check if OODA Terminal API is configured
  if (!sdk.oodaTerminal) {
    console.log('❌ OODA Terminal API not configured');
    console.log('   Set OODA_TERMINAL_ENDPOINT and OODA_TERMINAL_API_KEY environment variables');
    return;
  }
  
  console.log(`   Endpoint: ${sdk.config.endpoints.oodaTerminal}`);
  console.log();
  
  // Example site and terminal device
  const siteId = 'Sibaya';
  const terminalDeviceId = 'TERM-1000000054495190';
  
  try {
    // 1. Discover available data period
    console.log('📊 Discovering available data period...');
    const dataPeriod = await sdk.oodaTerminal.getDataPeriod({ site_id: siteId });
    console.log(`   Site: ${dataPeriod.site_id}`);
    console.log(`   First record: ${dataPeriod.first_record}`);
    console.log(`   Last record: ${dataPeriod.last_record}`);
    console.log();
    
    // 2. Query terminal alerts for the last 24 hours
    console.log('🔍 Querying terminal alerts (last 24 hours)...');
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - 24 * 60 * 60 * 1000);
    
    const timeRange = {
      start: startTime.toISOString(),
      end: endTime.toISOString()
    };
    
    const alerts = await sdk.oodaTerminal.getTerminalAlerts({
      terminal_device_id: terminalDeviceId,
      site_id: siteId,
      time_range: timeRange,
      resolution: '5min',
      limit: 10
    });
    
    console.log(`   Found ${alerts.length} alerts`);
    alerts.slice(0, 3).forEach(alert => {
      console.log(`   • ${alert.timestamp}: ${alert.alert_severity.toUpperCase()} - ${alert.message}`);
    });
    console.log();
    
    // 3. Query site alerts (all terminal devices)
    console.log('🏢 Querying site alerts (all terminal devices)...');
    const siteAlerts = await sdk.oodaTerminal.getSiteAlerts({
      site_id: siteId,
      time_range: timeRange,
      resolution: '5min',
      limit: 5
    });
    
    const totalAlerts = Object.values(siteAlerts).reduce((sum, deviceAlerts) => sum + deviceAlerts.length, 0);
    const deviceCount = Object.keys(siteAlerts).length;
    console.log(`   Found ${totalAlerts} alerts across ${deviceCount} terminal devices`);
    
    Object.entries(siteAlerts).slice(0, 2).forEach(([terminalId, deviceAlerts]) => {
      console.log(`   • ${terminalId}: ${deviceAlerts.length} alerts`);
    });
    console.log();
    
    // 4. Stream terminal alerts (demo for 30 seconds)
    console.log('📡 Streaming terminal alerts (30 seconds demo)...');
    console.log('   Press Ctrl+C to stop early');
    
    let streamCount = 0;
    const streamStart = Date.now();
    const streamTimeout = 30000; // 30 seconds
    
    try {
      for await (const alert of sdk.oodaTerminal.streamTerminal({
        terminal_device_id: terminalDeviceId,
        site_id: siteId,
        polling_interval: 5 // Poll every 5 seconds
      })) {
        streamCount++;
        console.log(`   📨 ${alert.timestamp}: ${alert.alert_severity.toUpperCase()} - ${alert.message}`);
        
        // Stop after 30 seconds for demo
        if (Date.now() - streamStart >= streamTimeout) {
          break;
        }
      }
    } catch (error) {
      if (error.code !== 'SIGINT') {
        throw error;
      }
      console.log('   Stream stopped by user');
    }
    
    console.log(`   Streamed ${streamCount} alerts`);
    console.log();
    
    // 5. Demonstrate cursor-based pagination
    console.log('📄 Demonstrating cursor-based pagination...');
    const pageSize = 3;
    let cursor = null;
    let pageNum = 1;
    
    while (pageNum <= 2) { // Show first 2 pages
      const pageAlerts = await sdk.oodaTerminal.getTerminalAlerts({
        terminal_device_id: terminalDeviceId,
        site_id: siteId,
        time_range: timeRange,
        limit: pageSize,
        cursor: cursor
      });
      
      if (pageAlerts.length === 0) {
        break;
      }
      
      console.log(`   Page ${pageNum}: ${pageAlerts.length} alerts`);
      pageAlerts.forEach(alert => {
        console.log(`     • ${alert.timestamp}: ${alert.message.substring(0, 50)}...`);
      });
      
      // Use the last alert's cursor for next page
      cursor = pageAlerts.length > 0 ? pageAlerts[pageAlerts.length - 1].cursor : null;
      pageNum++;
    }
    
    console.log();
    console.log('✅ OODA Terminal API example completed successfully!');
    
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
    console.log(`   Type: ${error.constructor.name}`);
    if (error.code) {
      console.log(`   Code: ${error.code}`);
    }
  }
}

// Handle Ctrl+C gracefully
process.on('SIGINT', () => {
  console.log('\n👋 Example interrupted by user');
  process.exit(0);
});

// Run the example
main().catch(error => {
  console.error('💥 Unhandled error:', error);
  process.exit(1);
});