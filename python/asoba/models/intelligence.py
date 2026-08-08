from typing import TypedDict, List, Optional

class CleaningEvent(TypedDict):
    timestamp: str
    jump_pct: float
    pr_before: float
    pr_after: float

class SoilingAudit(TypedDict):
    soiling_rate_pct_day: float
    detected_cleaning_events: List[CleaningEvent]
    recovery_gain_kwh_last_event: float

class Prognostics(TypedDict):
    battery_rul_days: Optional[int]
    battery_retirement_date: Optional[str]
    pv_annual_degradation_pct: float
    health_score: float

class BatteryKPIs(TypedDict):
    avg_soc: Optional[float]
    avg_soh: Optional[float]
    min_soh: Optional[float]
    max_soh: Optional[float]
    total_capacity_kwh: float
    warranty_status: str
    throughput_kwh: float
    warranty_remaining_pct: Optional[float]
    cycle_count_estimate: float
    dod_avg: Optional[float]
    asset_count: int

class SiteSummary(TypedDict):
    total_kWh_today: float
    fleet_availability_pct: float
    fleet_pr_pct: float
    active_inverters: int
    total_inverters: int
    last_updated: str
    battery: Optional[BatteryKPIs]
    soiling: Optional[SoilingAudit]
    prognostics: Optional[Prognostics]
