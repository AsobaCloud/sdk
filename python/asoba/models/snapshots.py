"""Snapshot data models for Ona Platform Partner API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EarKpis:
    energy_lost_kwh: float
    energy_lost_pct: float
    capacity_utilization_pct: float
    recovery_potential_kwh: dict[str, float]  # keys: "50pct", "75pct", "100pct"
    value_lost_zar: float
    realized_savings_zar: float
    annual_projection_zar: float

@dataclass
class FinancialKpis:
    tariff_currency: str
    shortfall_cost_zar: float
    realized_savings_zar: float
    total_potential_value_zar: float
    tou_breakdown: dict[str, Any]

@dataclass
class KpiRollupSnapshot:
    site_id: str
    period: dict[str, str]
    generated_at: str
    system: dict[str, Any]
    energy_balance: dict[str, Any]
    performance: dict[str, Any]
    ear: EarKpis
    financial: FinancialKpis
    battery: dict[str, Any] | None = None

@dataclass
class MaintenanceSignal:
    id: str
    timestamp: str
    asset_id: str
    type: str
    severity: str
    description: str
    state_code: str | None = None
    rated_kw: float | None = None
    expected_kw: float | None = None
    actual_kw: float | None = None
    capacity_pct: float | None = None
    irradiance_wm2: float | None = None

@dataclass
class MaintenanceSignalsSnapshot:
    site_id: str
    generated_at: str
    cursor: str
    signals: list[MaintenanceSignal]
    summary: dict[str, dict[str, int]]

@dataclass
class ForecastInterval:
    ts: str
    p50_kw: float
    p10_kw: float
    p90_kw: float
    revenue_zar: float

@dataclass
class ForecastSnapshot:
    site_id: str
    model_id: str
    generated_at: str
    horizon_hours: int
    resolution: str
    intervals: list[ForecastInterval]
    totals: dict[str, float]

@dataclass
class MaintenanceTask:
    asset_id: str
    task_type: str
    reason: str
    recommended_date: str
    priority: str
    estimated_duration_hours: float | None = None

@dataclass
class MaintenanceScheduleSnapshot:
    site_id: str
    generated_at: str
    horizon: dict[str, str]
    tasks: list[MaintenanceTask]
    summary: dict[str, Any]
