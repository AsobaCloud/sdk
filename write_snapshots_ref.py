import os

path = '/Users/shingi/Workbench/asobacloud.github.io/sdk/snapshots.md'
content = """---
title: "Snapshot Technical Reference"
layout: default
nav_order: 2
parent: "Ona SDK"
---

# Snapshot Technical Reference

The Ona Partner API and SDK use a **Pre-computed Snapshot Architecture** to deliver high-performance, analytical data to embedded dashboards and partner systems. This page details the format, delivery mechanism, and technical reasoning behind this approach.

---

## Architectural Philosophy
{: #architecture }

### Decoupling Compute from Delivery
Unlike the Telemetry and OODA Terminal APIs—which query live, raw time-series data—the Partner API serves data that has already been processed by the **Asset Intelligence Service**. 

This follows the **Backend-for-Frontend (BFF)** pattern:
1.  **Compute Phase**: Complex ML models and aggregation logic run hourly to generate site-level insights.
2.  **Persistence Phase**: These insights are stored as optimized JSON snapshots in S3.
3.  **Delivery Phase**: The Partner API acts as a thin delivery facade, reading these static files and serving them with high-performance headers.

### Why Snapshots?
*   **Performance**: Querying raw telemetry for a year-to-date KPI rollup in real-time is computationally expensive. Snapshots provide the result in sub-100ms.
*   **Reliability**: Dashboards can be rendered even if the underlying telemetry databases are under heavy load or maintenance.
*   **Consistency**: Partners receive the exact same "source of truth" used by Asoba's internal operations.

---

## Performance Optimization (ETag Caching)
{: #performance }

The primary performance enabler for the Partner API is the combination of **ETag-based conditional GETs** and **SDK-side in-memory caching**.

### The Flow
1.  **First Fetch**: The SDK requests a snapshot. The server returns `200 OK` with the JSON body and an `ETag` header (a hash of the file content).
2.  **SDK Cache**: The SDK stores the body and the ETag in a local `Map`.
3.  **Subsequent Fetches**: The SDK automatically adds the `If-None-Match: <etag>` header to the request.
4.  **Server Response**: 
    *   If the snapshot hasn't changed, the server returns `304 Not Modified` (empty body).
    *   The SDK then returns the data from its local cache immediately.

This reduces typical response times from **~150ms** (network + S3 read) to **<10ms** for cached data, while significantly reducing bandwidth consumption for embedded mobile users.

---

## Data Model & Formats
{: #data-model }

All snapshots are returned as JSON objects. Below are the standard shapes exposed by the `PartnerApiClient`.

### 1. KPI Rollup Snapshot (`getKpiRollup`)
Provides high-level performance metrics for a specific site, aggregated for the current day and year-to-date.

**Format Example:**
```json
{
  "site_id": "Sibaya",
  "timestamp": "2026-05-28T14:00:00Z",
  "kpis": {
    "daily_yield_kwh": 450.2,
    "ytd_yield_mwh": 124.5,
    "performance_ratio": 0.82,
    "availability_score": 0.99,
    "peak_power_kw": 85.0
  }
}
```

### 2. Maintenance Signals (`getMaintenanceSignals`)
Exposes pending health alerts and diagnostic findings that require operator attention.

**Format Example:**
```json
{
  "site_id": "Sibaya",
  "timestamp": "2026-05-28T14:00:00Z",
  "signals": [
    {
      "id": "SIG-123",
      "timestamp": "2026-05-28T10:15:00Z",
      "severity": "high",
      "message": "String 4 output 30% below expected vs local weather",
      "metadata": {
        "asset_id": "INV-001",
        "diagnostic_code": "UNDERPERFORMING_STRING",
        "recommended_action": "Check DC connections and soiling"
      }
    }
  ]
}
```

### 3. Forecast Snapshot (`getForecastSnapshot`)
Provides a pre-computed energy generation forecast for the site, typically covering a 24-hour or 7-day horizon.

**Format Example:**
```json
{
  "site_id": "Sibaya",
  "timestamp": "2026-05-28T14:00:00Z",
  "horizon": "24h",
  "forecasts": [
    {"timestamp": "2026-05-28T15:00:00Z", "expected_power_kw": 45.2},
    {"timestamp": "2026-05-28T16:00:00Z", "expected_power_kw": 38.5}
  ]
}
```

---

## Generic Snapshot Access
{: #generic-snapshots }

The `getSnapshot({ site_id, kind })` method allows access to experimental or custom snapshots produced by Asoba research teams before they are promoted to formal SDK methods. Use the `kind` parameter to specify the sub-folder in the snapshot store (e.g., `kind: "custom-site-health"`).
"""

with open(path, 'w') as f:
    f.write(content)
"""
