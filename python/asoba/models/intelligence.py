
from __future__ import annotations

from typing import TypedDict


class CleaningEvent(TypedDict):
    timestamp: str
    jump_pct: float
    pr_before: float
    pr_after: float

class SoilingAudit(TypedDict):
    soiling_rate_pct_day: float
    detected_cleaning_events: list[CleaningEvent]
    recovery_gain_kwh_last_event: float

class Prognostics(TypedDict):
    battery_rul_days: int | None
    battery_retirement_date: str | None
    pv_annual_degradation_pct: float
    health_score: float

class BatteryKPIs(TypedDict):
    avg_soc: float | None
    avg_soh: float | None
    min_soh: float | None
    max_soh: float | None
    total_capacity_kwh: float
    warranty_status: str
    throughput_kwh: float
    warranty_remaining_pct: float | None
    cycle_count_estimate: float
    dod_avg: float | None
    asset_count: int

class SiteSummary(TypedDict):
    total_kWh_today: float
    fleet_availability_pct: float
    fleet_pr_pct: float
    active_inverters: int
    total_inverters: int
    last_updated: str
    battery: BatteryKPIs | None
    soiling: SoilingAudit | None
    prognostics: Prognostics | None
