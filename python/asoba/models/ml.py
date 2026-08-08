"""ML and training data models for Ona Platform SDK."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GapDetectionResult:
    customer_id: str
    scan_period: dict[str, str]
    gaps_found: list[dict[str, Any]]
    dates_needing_backfill: list[str]
    total_missing_intervals: int
    needs_backfill: bool
    client_id: str | None = None
    region: str | None = None
    location: str | None = None
    manufacturer: str | None = None
    device_count: int | None = None
    devices_scanned: list[str] | None = None
    backfill_targets: dict[str, list[str]] | None = None

@dataclass
class TrainingStatusResponse:
    customer_id: str
    status: str
    processing_job_name: str | None
    last_updated: str | None
    training_job_name: str | None = None
    processing_progress: dict[str, Any] | None = None
    training_progress: dict[str, Any] | None = None

@dataclass
class TrainResponseBatch:
    message: str
    jobs_started: int
    jobs_failed: int
    jobs_skipped: int
    total_requested: int
    jobs: list[dict[str, str]]
    note: str
    failures: list[dict[str, str]] | None = None
    skipped: list[dict[str, str]] | None = None
