from __future__ import annotations

from job_mentor.collectors.base import BaseCollector
from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.models.job import Job
from job_mentor.utils.dates import is_within_search_window


def collect_jobs_for_window(
    collector: BaseCollector,
    repository: SQLiteJobRepository,
    terms: list[str] | None = None,
    days: int = 14,
) -> list[Job]:
    jobs = collector.search_jobs(terms=terms, days=days)
    stored: list[Job] = []

    for job in jobs:
        if not is_within_search_window(job.posted_date, days=days):
            continue

        duplicate = repository.find_duplicate_job(job)
        if duplicate is None:
            saved = repository.insert_job(job)
        else:
            saved = repository.upsert_job(job)
        stored.append(saved)

    return stored
