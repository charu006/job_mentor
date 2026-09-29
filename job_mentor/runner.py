from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable

from job_mentor.collectors import BaseCollector
from job_mentor.config.settings import load_settings, settings
from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.matching.engine import MatchingEngine
from job_mentor.models.job import Job
from job_mentor.utils.dates import is_within_search_window

logger = logging.getLogger("job_mentor.runner")


@dataclass
class CollectionRunSummary:
    run_started_at: datetime
    timezone_name: str
    collectors_attempted: int = 0
    collectors_skipped: int = 0
    successful_collectors: list[str] = field(default_factory=list)
    failed_collectors: list[str] = field(default_factory=list)
    raw_jobs_collected: int = 0
    jobs_in_window: int = 0
    relevant_jobs: int = 0
    new_jobs: int = 0
    duplicates: int = 0
    below_threshold: int = 0
    invalid_jobs: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "run_started_at": self.run_started_at.isoformat(),
            "timezone_name": self.timezone_name,
            "collectors_attempted": self.collectors_attempted,
            "collectors_skipped": self.collectors_skipped,
            "successful_collectors": list(self.successful_collectors),
            "failed_collectors": list(self.failed_collectors),
            "raw_jobs_collected": self.raw_jobs_collected,
            "jobs_in_window": self.jobs_in_window,
            "relevant_jobs": self.relevant_jobs,
            "new_jobs": self.new_jobs,
            "duplicates": self.duplicates,
            "below_threshold": self.below_threshold,
            "invalid_jobs": self.invalid_jobs,
        }


def discover_collector_classes() -> list[type[BaseCollector]]:
    import job_mentor.collectors as collectors_module

    collector_classes: list[type[BaseCollector]] = []
    for name in getattr(collectors_module, "__all__", []):
        obj = getattr(collectors_module, name, None)
        if isinstance(obj, type) and issubclass(obj, BaseCollector) and obj is not BaseCollector:
            collector_classes.append(obj)
    return collector_classes


def discover_collectors() -> list[BaseCollector]:
    collectors: list[BaseCollector] = []
    for collector_class in discover_collector_classes():
        try:
            collector = collector_class()
        except TypeError:
            try:
                collector = collector_class(enabled=False)
            except TypeError:
                collector = collector_class(base_url=None)
        if not hasattr(collector, "enabled"):
            collector.enabled = False
        collectors.append(collector)
    return collectors


def _collector_name(collector: BaseCollector) -> str:
    return getattr(collector, "source_name", collector.__class__.__name__)


def _normalize_collector_result(raw_job: Any, collector: BaseCollector) -> Job | None:
    if raw_job is None:
        return None
    if isinstance(raw_job, Job):
        return raw_job
    if isinstance(raw_job, dict):
        normalized = collector.normalize_raw_job(raw_job)
        if normalized is None:
            return None
        return normalized
    return None


def run_collection(
    db_path: str | None = None,
    collectors: Iterable[BaseCollector] | None = None,
    days: int | None = None,
) -> CollectionRunSummary:
    active_settings = load_settings()
    if days is None:
        days = getattr(active_settings, "search_window_days", 14)

    repository = SQLiteJobRepository(db_path or active_settings.database_path)
    repository.initialize_database()
    engine = MatchingEngine()

    run_start = datetime.now(timezone.utc)
    summary = CollectionRunSummary(
        run_started_at=run_start,
        timezone_name=getattr(active_settings, "timezone", "Europe/Berlin"),
    )

    if collectors is None:
        collectors = discover_collectors()

    for collector in collectors:
        collector_name = _collector_name(collector)
        enabled = bool(getattr(collector, "enabled", False))
        if not enabled:
            summary.collectors_skipped += 1
            logger.info("Skipping disabled collector: %s", collector_name)
            continue

        summary.collectors_attempted += 1
        try:
            search_terms = getattr(collector, "search_terms", None)
            raw_jobs = collector.search_jobs(terms=search_terms, days=days)
            if raw_jobs is None:
                raw_jobs = []
        except Exception as exc:
            summary.failed_collectors.append(collector_name)
            logger.exception("Collector %s failed: %s", collector_name, exc)
            continue

        successful_jobs: list[Job] = []
        for raw_job in raw_jobs:
            normalized = _normalize_collector_result(raw_job, collector)
            if normalized is None:
                summary.invalid_jobs += 1
                continue

            summary.raw_jobs_collected += 1
            if not is_within_search_window(normalized.posted_date, days=days):
                continue
            summary.jobs_in_window += 1

            engine.score_job(normalized)
            if normalized.match_score < 40:
                summary.below_threshold += 1
                continue

            duplicate = repository.find_duplicate_job(normalized)
            if duplicate is not None:
                summary.duplicates += 1
                repository.upsert_job(normalized)
            else:
                repository.insert_job(normalized)
                summary.new_jobs += 1

            summary.relevant_jobs += 1
            successful_jobs.append(normalized)

        if successful_jobs or not raw_jobs:
            summary.successful_collectors.append(collector_name)
        else:
            summary.failed_collectors.append(collector_name)

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Job Mentor collection pipeline.")
    parser.add_argument("--db", dest="db_path", default=None, help="Path to the SQLite database file.")
    parser.add_argument("--days", dest="days", type=int, default=None, help="Override the 14-day collection window.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    summary = run_collection(db_path=args.db_path, days=args.days)

    print("Job Mentor collection run")
    print("========================")
    print(f"Started: {summary.run_started_at.isoformat()}")
    print(f"Timezone: {summary.timezone_name}")
    print()
    print("Collectors:")
    for collector in discover_collectors():
        name = _collector_name(collector)
        if not getattr(collector, "enabled", False):
            print(f"  {name:<24} SKIPPED (disabled)")
        elif name in summary.successful_collectors:
            print(f"  {name:<24} OK")
        elif name in summary.failed_collectors:
            print(f"  {name:<24} FAILED")
        else:
            print(f"  {name:<24} OK")

    print()
    print("Results:")
    print(f"  Raw jobs: {summary.raw_jobs_collected}")
    print(f"  Within {settings.search_window_days if hasattr(settings, 'search_window_days') else 14} days: {summary.jobs_in_window}")
    print(f"  Relevant: {summary.relevant_jobs}")
    print(f"  New: {summary.new_jobs}")
    print(f"  Duplicates: {summary.duplicates}")
    print(f"  Failed collectors: {len(summary.failed_collectors)}")

    return 0
