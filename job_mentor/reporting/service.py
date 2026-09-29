from __future__ import annotations

from datetime import datetime, timezone

from job_mentor.config.settings import settings
from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.models.job import Job
from job_mentor.reporting.model import DailyReport, DailyReportJob
from job_mentor.timezone_utils import germany_date_string, utc_now
from job_mentor.utils.dates import is_within_search_window, normalize_datetime


class DailyReportService:
    def __init__(self, repository: SQLiteJobRepository | None = None):
        self.repository = repository

    @staticmethod
    def _as_report_job(job: Job) -> DailyReportJob:
        return DailyReportJob(
            id=getattr(job, "id", None),
            title=job.title,
            company=job.company,
            location=job.location,
            country=job.country,
            source=job.source,
            source_job_id=getattr(job, "source_job_id", None),
            url=job.url,
            description=getattr(job, "description", None),
            posted_date=job.posted_date,
            deadline=getattr(job, "deadline", None),
            discovered_at=getattr(job, "discovered_at", None),
            first_seen_at=getattr(job, "first_seen_at", None),
            last_seen_at=getattr(job, "last_seen_at", None),
            notified_at=getattr(job, "notified_at", None),
            match_score=float(job.match_score or 0.0),
            match_reasons=list(job.match_reasons or []),
            status=getattr(job, "status", "new"),
            canonical_url=getattr(job, "canonical_url", None),
            fingerprint=getattr(job, "fingerprint", None),
        )

    @staticmethod
    def _effective_sort_date(job: Job):
        for candidate in (job.posted_date, job.discovered_at, job.first_seen_at, job.last_seen_at):
            dt = normalize_datetime(candidate)
            if dt is not None:
                return dt
        return datetime.min.replace(tzinfo=timezone.utc)

    @staticmethod
    def _window_reference(job: Job):
        return DailyReportService._effective_sort_date(job)

    @staticmethod
    def _sort_key(job: Job):
        effective = DailyReportService._effective_sort_date(job)
        return (-effective.date().toordinal(), (job.title or "").lower(), (job.source_job_id or ""))

    def _filter_jobs(self, jobs: list[Job], days: int, minimum_score: int = 40) -> list[DailyReportJob]:
        report_jobs: list[DailyReportJob] = []
        for job in jobs:
            if job is None or not job.title:
                continue
            if job.match_score is None or float(job.match_score) < minimum_score:
                continue
            if not is_within_search_window(self._window_reference(job), days=days):
                continue
            report_jobs.append(self._as_report_job(job))

        report_jobs.sort(key=lambda job: self._sort_key(Job(title=job.title, source_job_id=job.source_job_id, posted_date=job.posted_date, discovered_at=job.discovered_at, first_seen_at=job.first_seen_at, last_seen_at=job.last_seen_at)))
        return report_jobs

    def build_report(self, report_date: str | None = None, days: int | None = None, minimum_score: int = 40) -> DailyReport:
        if self.repository is None:
            return DailyReport(
                report_date=report_date or germany_date_string(),
                timezone="Europe/Berlin",
                generated_at=utc_now(),
                search_window_days=days or getattr(settings, "search_window_days", 14),
                jobs=[],
            )

        target_days = days if days is not None else getattr(settings, "search_window_days", 14)
        jobs = self.repository.get_jobs_within_date_window(days=target_days)
        filtered = [job for job in jobs if job is not None and job.match_score is not None and float(job.match_score) >= minimum_score]
        filtered = [job for job in filtered if is_within_search_window(self._window_reference(job), days=target_days)]
        filtered.sort(key=self._sort_key)
        report_jobs = [self._as_report_job(job) for job in filtered]
        return DailyReport(
            report_date=report_date or germany_date_string(),
            timezone="Europe/Berlin",
            generated_at=utc_now(),
            search_window_days=target_days,
            jobs=report_jobs,
        )

    def get_initial_report(self, report_date: str | None = None, days: int = 14, minimum_score: int = 40) -> DailyReport:
        return self.build_report(report_date=report_date, days=days, minimum_score=minimum_score)

    def get_daily_report(self, report_date: str | None = None, days: int = 14, include_reported: bool = False, minimum_score: int = 40) -> DailyReport:
        if self.repository is None:
            return DailyReport(
                report_date=report_date or germany_date_string(),
                timezone="Europe/Berlin",
                generated_at=utc_now(),
                search_window_days=days,
                jobs=[],
            )

        if include_reported:
            jobs = self.repository.get_jobs_within_date_window(days=days)
        else:
            jobs = [job for job in self.repository.get_unnotified_jobs() if job is not None]

        filtered = [job for job in jobs if job is not None and job.match_score is not None and float(job.match_score) >= minimum_score]
        filtered = [job for job in filtered if is_within_search_window(self._window_reference(job), days=days)]
        filtered.sort(key=self._sort_key)
        report_jobs = [self._as_report_job(job) for job in filtered]
        return DailyReport(
            report_date=report_date or germany_date_string(),
            timezone="Europe/Berlin",
            generated_at=utc_now(),
            search_window_days=days,
            jobs=report_jobs,
        )
