from __future__ import annotations

from datetime import datetime

from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.models.job import Job
from job_mentor.reporting.model import DailyJobReport
from job_mentor.timezone_utils import germany_date_string, utc_now


class DailyReportService:
    def __init__(self, repository: SQLiteJobRepository | None = None):
        self.repository = repository

    def get_initial_report(self, report_date: str | None = None, days: int = 14) -> DailyJobReport:
        if self.repository is None:
            return DailyJobReport(report_date=report_date or germany_date_string(), timezone="Europe/Berlin", generated_at=utc_now(), jobs=[])

        jobs = self.repository.get_jobs_within_date_window(days=days)
        return DailyJobReport(
            report_date=report_date or germany_date_string(),
            timezone="Europe/Berlin",
            generated_at=utc_now(),
            jobs=jobs,
        )

    def get_daily_report(self, report_date: str | None = None, days: int = 14, include_reported: bool = False) -> DailyJobReport:
        if self.repository is None:
            return DailyJobReport(report_date=report_date or germany_date_string(), timezone="Europe/Berlin", generated_at=utc_now(), jobs=[])

        if include_reported:
            jobs = self.repository.get_jobs_within_date_window(days=days)
        else:
            jobs = [job for job in self.repository.get_unnotified_jobs() if job is not None]

        return DailyJobReport(
            report_date=report_date or germany_date_string(),
            timezone="Europe/Berlin",
            generated_at=utc_now(),
            jobs=jobs,
        )
