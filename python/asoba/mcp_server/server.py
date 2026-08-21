"""MCP server that wraps the Asoba/Ona Platform SDK.

Exposes inverter telemetry, OODA terminal alerts, partner API snapshots,
and forecasting as MCP tools.  JSON schemas are served as MCP resources
so the LLM can inspect response shapes on demand.

Transport: stdio (JSON-RPC over stdin/stdout).
Auth: ASOBA_API_KEY environment variable.
"""

from __future__ import annotations

import dataclasses
import json
import logging
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

logger = logging.getLogger("asoba.mcp_server")

# ---------------------------------------------------------------------------
# Schema directory (bundled with the package)
# ---------------------------------------------------------------------------
_SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"


# ---------------------------------------------------------------------------
# JSON-serialisation helper
# ---------------------------------------------------------------------------

def _ser(obj: Any) -> str:
    """Serialize SDK objects (dataclasses, dicts, lists, primitives) to JSON."""
    def _convert(o: Any) -> Any:
        if dataclasses.is_dataclass(o) and not isinstance(o, type):
            return {k: _convert(v) for k, v in dataclasses.asdict(o).items()}
        if isinstance(o, dict):
            return {k: _convert(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_convert(v) for v in o]
        return o

    return json.dumps(_convert(obj), default=str, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Lazy client singleton
# ---------------------------------------------------------------------------
_client = None


def _get_client():
    global _client
    if _client is None:
        from asoba import OnaClient

        _client = OnaClient()
        logger.info("OnaClient initialised")
    return _client


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

server = MCPServer(
    name="asoba",
    version="1.0.0",
    description=(
        "Ona Energy Management Platform \u2014 inverter telemetry, OODA alerts, "
        "KPI rollups, maintenance signals, and forecasting."
    ),
    instructions=(
        "Use these tools to query solar energy data for Asoba platform sites. "
        "Call get_telemetry_data_period or get_ooda_data_period first to "
        "discover available time ranges for a site before querying. "
        "Read schema://<name> resources to inspect response JSON schemas."
    ),
)


# ===================================================================
# Tools \u2014 Inverter Telemetry
# ===================================================================


@server.tool()
def get_telemetry_data_period(
    site_id: str,
    asset_id: str | None = None,
) -> str:
    """Discover the earliest and latest available telemetry timestamps for a site or inverter.

    Call this before get_inverter_telemetry to find what time range has data.
    Returns a dict with first_record and last_record ISO timestamps.
    """
    client = _get_client()
    result = client.inverter_telemetry.get_data_period(
        site_id=site_id, asset_id=asset_id,
    )
    return _ser(result)


@server.tool()
def get_inverter_telemetry(
    asset_id: str,
    site_id: str,
    start: str,
    end: str,
    resolution: str = "5min",
    limit: int = 100,
) -> str:
    """Query inverter-level telemetry records.

    Args:
        asset_id: Inverter asset identifier (e.g. INV-1000000054495190).
        site_id: Site identifier (e.g. Sibaya).
        start: Start of time range (ISO 8601, e.g. 2025-11-01T00:00:00Z).
        end: End of time range (ISO 8601).
        resolution: Aggregation resolution \u2014 5min (default), 15min, 1h, 1d.
        limit: Max records to return (1\u20131000, default 100).

    Returns JSON array of telemetry records with timestamp, power_kw, voltage, current, etc.
    """
    from asoba.models.telemetry import TimeRange

    client = _get_client()
    records = client.inverter_telemetry.get_inverter_telemetry(
        asset_id=asset_id,
        site_id=site_id,
        time_range=TimeRange(start=start, end=end),
        resolution=resolution,
        limit=min(limit, 1000),
    )
    return _ser(records)


@server.tool()
def get_site_telemetry(
    site_id: str,
    start: str,
    end: str,
    resolution: str = "5min",
    limit: int = 100,
) -> str:
    """Query all inverter telemetry for a site.

    Returns a dict keyed by asset_id, each value being an array of telemetry records.
    """
    from asoba.models.telemetry import TimeRange

    client = _get_client()
    result = client.inverter_telemetry.get_site_telemetry(
        site_id=site_id,
        time_range=TimeRange(start=start, end=end),
        resolution=resolution,
        limit=min(limit, 1000),
    )
    return _ser(result)


# ===================================================================
# Tools \u2014 OODA Terminal Alerts
# ===================================================================


@server.tool()
def get_ooda_data_period(
    site_id: str,
    terminal_device_id: str | None = None,
) -> str:
    """Discover the earliest and latest available OODA alert timestamps for a site or terminal device.

    Call this before get_terminal_alerts to find what time range has data.
    """
    client = _get_client()
    result = client.ooda_terminal.get_data_period(
        site_id=site_id, terminal_device_id=terminal_device_id,
    )
    return _ser(result)


@server.tool()
def get_terminal_alerts(
    terminal_device_id: str,
    site_id: str,
    start: str,
    end: str,
    resolution: str = "5min",
    limit: int = 100,
) -> str:
    """Query OODA terminal alerts for a specific terminal device.

    These are the raw state-detection events (fault, warning, normal transitions)
    produced by the OODA pipeline for an individual terminal device.

    Args:
        terminal_device_id: Terminal device identifier.
        site_id: Site identifier.
        start: Start of time range (ISO 8601).
        end: End of time range (ISO 8601).
        resolution: Aggregation resolution (default 5min).
        limit: Max alerts to return (1\u20131000).
    """
    from asoba.models.ooda import TimeRange

    client = _get_client()
    alerts = client.ooda_terminal.get_terminal_alerts(
        terminal_device_id=terminal_device_id,
        site_id=site_id,
        time_range=TimeRange(start=start, end=end),
        resolution=resolution,
        limit=min(limit, 1000),
    )
    return _ser(alerts)


@server.tool()
def get_site_alerts(
    site_id: str,
    start: str,
    end: str,
    resolution: str = "5min",
    limit: int = 100,
) -> str:
    """Query OODA alerts for all terminal devices at a site.

    Returns a dict keyed by terminal_device_id, each value being an array of alerts.
    """
    from asoba.models.ooda import TimeRange

    client = _get_client()
    result = client.ooda_terminal.get_site_alerts(
        site_id=site_id,
        time_range=TimeRange(start=start, end=end),
        resolution=resolution,
        limit=min(limit, 1000),
    )
    return _ser(result)


# ===================================================================
# Tools \u2014 Partner API (pre-computed snapshots)
# ===================================================================


@server.tool()
def get_kpi_rollup(site_id: str) -> str:
    """Get the latest KPI rollup snapshot for a site.

    Includes energy balance (consumption, solar production, grid purchases, offset %),
    performance ratios, true/state uptime, availability, energy-at-risk metrics,
    financial impact (ZAR), and battery health (if applicable).
    """
    client = _get_client()
    result = client.partner.get_kpi_rollup(site_id=site_id)
    return _ser(result)


@server.tool()
def get_maintenance_signals(
    site_id: str,
    since: str | None = None,
    severity: str | None = None,
) -> str:
    """Get enriched maintenance signals for a site.

    These are intelligence-layer interpretations derived from raw OODA/JEPA state
    detections via rolling-window analysis. Signal types: Critical State, Warning State,
    Temperature, Capacity Underperformance, Zero Production. Each signal carries
    severity, expected vs actual kW, capacity %, and irradiance context.

    Args:
        site_id: Site identifier.
        since: Optional ISO timestamp to filter signals after this time.
        severity: Optional severity filter (Critical, High, Medium, Low).
    """
    client = _get_client()
    result = client.partner.get_maintenance_signals(
        site_id=site_id, since=since, severity=severity,
    )
    return _ser(result)


@server.tool()
def get_maintenance_schedule(
    site_id: str,
    since: str | None = None,
) -> str:
    """Get the preventive maintenance schedule for a site.

    A forward-looking 90-day task list derived from maintenance signals.
    Tasks are grouped by asset with priority, recommended date, and task type
    (inspection, corrective_maintenance, scheduled_service).
    """
    client = _get_client()
    result = client.partner.get_maintenance_schedule(
        site_id=site_id, since=since,
    )
    return _ser(result)


@server.tool()
def get_forecast_snapshot(
    site_id: str,
    horizon: str | None = None,
) -> str:
    """Get the latest forecast snapshot for a site.

    Args:
        site_id: Site identifier.
        horizon: Optional forecast horizon filter.
    """
    client = _get_client()
    result = client.partner.get_forecast_snapshot(
        site_id=site_id, horizon=horizon,
    )
    return _ser(result)


# ===================================================================
# Tools \u2014 Forecasting
# ===================================================================


@server.tool()
def get_device_forecast(
    site_id: str,
    device_id: str,
    forecast_hours: int = 24,
) -> str:
    """Get a solar energy forecast for a specific device.

    Args:
        site_id: Site identifier.
        device_id: Device/inverter identifier.
        forecast_hours: Number of hours to forecast (default 24).
    """
    client = _get_client()
    result = client.forecasting.get_device_forecast(
        site_id=site_id,
        device_id=device_id,
        forecast_hours=forecast_hours,
    )
    return _ser(result)


@server.tool()
def get_site_forecast(
    site_id: str,
    forecast_hours: int = 24,
    include_device_breakdown: bool = False,
) -> str:
    """Get an aggregated solar energy forecast for an entire site.

    Args:
        site_id: Site identifier.
        forecast_hours: Number of hours to forecast (default 24).
        include_device_breakdown: Include individual device-level forecasts.
    """
    client = _get_client()
    result = client.forecasting.get_site_forecast(
        site_id=site_id,
        forecast_hours=forecast_hours,
        include_device_breakdown=include_device_breakdown,
    )
    return _ser(result)


# ===================================================================
# Resources \u2014 JSON Schemas
# ===================================================================


@server.resource("schema://KPIRollup", name="KPIRollup", description="JSON schema for site-level KPI rollup snapshots", mime_type="application/json")
def _res_kpi() -> str:
    return (_SCHEMAS_DIR / "KPIRollup.json").read_text()


@server.resource("schema://MaintenanceSignals", name="MaintenanceSignals", description="JSON schema for maintenance signal snapshots", mime_type="application/json")
def _res_maint_signals() -> str:
    return (_SCHEMAS_DIR / "MaintenanceSignals.json").read_text()


@server.resource("schema://MaintenanceSchedule", name="MaintenanceSchedule", description="JSON schema for maintenance schedule snapshots", mime_type="application/json")
def _res_maint_schedule() -> str:
    return (_SCHEMAS_DIR / "MaintenanceSchedule.json").read_text()


@server.resource("schema://ForecastSnapshot", name="ForecastSnapshot", description="JSON schema for forecast snapshots", mime_type="application/json")
def _res_forecast_snapshot() -> str:
    return (_SCHEMAS_DIR / "ForecastSnapshot.json").read_text()


@server.resource("schema://StandardizedTelemetry", name="StandardizedTelemetry", description="JSON schema for inverter telemetry records", mime_type="application/json")
def _res_telemetry() -> str:
    return (_SCHEMAS_DIR / "StandardizedTelemetry.json").read_text()


@server.resource("schema://ODSERecord", name="ODSERecord", description="JSON schema for OODA terminal alert records", mime_type="application/json")
def _res_odse() -> str:
    return (_SCHEMAS_DIR / "ODSERecord.json").read_text()


# ===================================================================
# Entry point
# ===================================================================


def run():
    """Start the MCP server on stdio transport."""
    server.run(transport="stdio")


if __name__ == "__main__":
    run()
