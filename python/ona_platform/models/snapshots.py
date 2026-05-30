"""Snapshot data models for Ona Platform Partner API."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class KpiRollupSnapshot:
    site_id: str
    period: Dict[str, str]
    generated_at: str
    system: Dict[str, Any]
    energy_balance: Dict[str, Any]
    performance: Dict[str, Any]
    ear: Dict[str, Any]
    financial: Dict[str, Any]

@dataclass
class MaintenanceSignal:
    id: str
    timestamp: str
    asset_id: str
    type: str
    severity: str
    description: str
    state_code: Optional[str] = None
    rated_kw: Optional[float] = None
    expected_kw: Optional[float] = None
    actual_kw: Optional[float] = None
    capacity_pct: Optional[float] = None
    irradiance_wm2: Optional[float] = None

@dataclass
class MaintenanceSignalsSnapshot:
    site_id: str
    generated_at: str
    cursor: str
    signals: List[MaintenanceSignal]
    summary: Dict[str, Dict[str, int]]

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
    intervals: List[ForecastInterval]
    totals: Dict[str, float]

@dataclass
class MaintenanceTask:
    asset_id: str
    task_type: str
    reason: str
    recommended_date: str
    priority: str
    estimated_duration_hours: Optional[float] = None

@dataclass
class MaintenanceScheduleSnapshot:
    site_id: str
    generated_at: str
    horizon: Dict[str, str]
    tasks: List[MaintenanceTask]
    summary: Dict[str, Any]
