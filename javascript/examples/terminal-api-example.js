/**
 * Terminal API (OODA Workflow) Example
 * Demonstrates the complete OODA loop: Observe, Orient, Decide, Act
 */

const { OnaSDK } = require('../src/index');

async function main() {
  const sdk = new OnaSDK({
    region: 'af-south-1',
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
    },
    endpoints: {
      terminal: process.env.ONA_TERMINAL_ENDPOINT || 'https://terminal.api.asoba.co'
    }
  });

  const customerId = 'customer123';

  try {
    // Step 1: List and add assets
    console.log('=== Asset Management ===\n');

    const assetsResult = await sdk.terminal.listAssets({ customer_id: customerId });
    console.log(`Current assets: ${assetsResult.assets.length}`);

    // Add a new asset (example)
    if (assetsResult.assets.length === 0) {
      const newAsset = await sdk.terminal.addAsset({
        customer_id: customerId,
        asset_id: 'INV-DEMO-001',
        name: 'Demo Solar Inverter',
        type: 'inverter',
        capacity_kw: 150,
        location: 'Durban, South Africa',
        timezone: 'Africa/Johannesburg'
      });
      console.log(`✓ Created demo asset: ${newAsset.asset_id}`);
    }

    const assetId = assetsResult.assets.length > 0
      ? assetsResult.assets[0].asset_id
      : 'INV-DEMO-001';

    // Step 2: OBSERVE - Run fault detection
    console.log('\n=== OBSERVE Phase: Fault Detection ===\n');

    const detection = await sdk.terminal.runDetection({
      customer_id: customerId,
      asset_id: assetId,
      lookback_hours: 6
    });

    console.log(`Detection ID: ${detection.detection_id}`);
    console.log(`Severity: ${detection.analysis.severity_label} (${(detection.analysis.severity_score * 100).toFixed(1)}%)`);
    console.log(`Status: ${detection.analysis.status}`);
    console.log(`Summary: ${detection.analysis.summary}`);

    if (detection.analysis.energy_at_risk_kw) {
      console.log(`Energy at risk: ${detection.analysis.energy_at_risk_kw} kW`);
    }

    // Step 3: ORIENT - Run diagnostics
    console.log('\n=== ORIENT Phase: Diagnostics ===\n');

    const diagnostic = await sdk.terminal.runDiagnostics({
      customer_id: customerId,
      asset_id: assetId,
      detection_id: detection.detection_id,
      lookback_hours: 6
    });

    console.log(`Diagnostic ID: ${diagnostic.diagnostic_id}`);
    console.log(`Root cause: ${diagnostic.analysis.root_cause}`);
    console.log(`Category: ${diagnostic.analysis.category}`);
    console.log(`Confidence: ${(diagnostic.analysis.confidence * 100).toFixed(1)}%`);
    console.log(`Summary: ${diagnostic.analysis.summary}`);

    if (diagnostic.analysis.recommended_actions) {
      console.log('\nRecommended actions:');
      diagnostic.analysis.recommended_actions.forEach((action, i) => {
        console.log(`  ${i + 1}. ${action}`);
      });
    }

    // Step 4: DECIDE - Create maintenance schedule
    console.log('\n=== DECIDE Phase: Maintenance Scheduling ===\n');

    const schedule = await sdk.terminal.createSchedule({
      customer_id: customerId,
      asset_id: assetId,
      title: 'Repair faulty inverter',
      priority: 'High',
      description: `Based on diagnostic ${diagnostic.diagnostic_id}: ${diagnostic.analysis.root_cause}`,
      estimated_duration_hours: 4
    });

    console.log(`✓ Schedule created: ${schedule.schedule_id}`);

    // Step 5: ACT - Build BOM and create order
    console.log('\n=== ACT Phase: Bill of Materials & Work Order ===\n');

    const bom = await sdk.terminal.buildBOM({
      customer_id: customerId,
      asset_id: assetId,
      schedule_id: schedule.schedule_id
    });

    console.log(`✓ BOM created: ${bom.bom_id}`);
    console.log(`Estimated cost: $${bom.total_cost_usd}`);

    const order = await sdk.terminal.createOrder({
      customer_id: customerId,
      asset_id: assetId,
      bom_id: bom.bom_id
    });

    console.log(`✓ Work order created: ${order.order_id}`);

    // Step 6: Get real-time monitoring data
    console.log('\n=== Real-Time Monitoring ===\n');

    const nowcast = await sdk.terminal.getNowcastData({
      customer_id: customerId,
      time_range: '1h'
    });

    if (nowcast.success && nowcast.data.latest_metrics) {
      const metrics = nowcast.data.latest_metrics;
      console.log(`Total power: ${metrics.total_power_kw} kW`);
      console.log(`Average temperature: ${metrics.avg_temperature_c}°C`);
      console.log(`Capacity factor: ${metrics.avg_capacity_factor}%`);
      console.log(`Active inverters: ${metrics.active_inverters}/${metrics.total_inverters}`);
      console.log(`Last updated: ${metrics.last_updated}`);
    }

    // Step 7: List all activities
    console.log('\n=== Activity Stream (All OODA Phases) ===\n');

    const activities = await sdk.terminal.listActivities({
      customer_id: customerId
    });

    console.log(`Total activities (24h): ${activities.count}`);
    if (activities.activities.length > 0) {
      console.log('\nRecent activities:');
      activities.activities.slice(0, 5).forEach(activity => {
        console.log(`  [${activity.phase.toUpperCase()}] ${activity.title}`);
        console.log(`    ${activity.description}`);
        console.log(`    ${activity.timestamp}\n`);
      });
    }

  } catch (error) {
    console.error('Error:', error.message);
    if (error.code) {
      console.error('Error code:', error.code);
    }
    if (error.statusCode) {
      console.error('HTTP status:', error.statusCode);
    }
    if (error.details) {
      console.error('Details:', error.details);
    }
  }
}

main().catch(console.error);
