"""ML and training data models for Ona Platform SDK."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class GapDetectionResult:
    customer_id: str
    scan_period: Dict[str, str]
    gaps_found: List[Dict[str, Any]]
    dates_needing_backfill: List[str]
    total_missing_intervals: int
    needs_backfill: bool
    client_id: Optional[str] = None
    region: Optional[str] = None
    location: Optional[str] = None
    manufacturer: Optional[str] = None
    device_count: Optional[int] = None
    devices_scanned: Optional[List[str]] = None
    backfill_targets: Optional[Dict[str, List[str]]] = None

@dataclass
class TrainingStatusResponse:
    customer_id: str
    status: str
    processing_job_name: Optional[str]
    last_updated: Optional[str]
    training_job_name: Optional[str] = None
    processing_progress: Optional[Dict[str, Any]] = None
    training_progress: Optional[Dict[str, Any]] = None

@dataclass
class TrainResponseBatch:
    message: str
    jobs_started: int
    jobs_failed: int
    jobs_skipped: int
    total_requested: int
    jobs: List[Dict[str, str]]
    note: str
    failures: Optional[List[Dict[str, str]]] = None
    skipped: Optional[List[Dict[str, str]]] = None
