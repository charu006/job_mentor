from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from job_mentor.models.job import Job


@dataclass
class DailyReportJob:
    title: str | None = None
    company: str | None = None
    location: str | None = None
    country: str | None = None
    source: str | None = None
    source_job_id: str | None = None
    url: str | None = None
    description: str | None = None
    posted_date: date | datetime | str | None = None
    deadline: date | datetime | str | None = None
    discovered_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    notified_at: datetime | None = None
    match_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)
    status: str = "new"
    id: int | None = None
    canonical_url: str | None = None
    fingerprint: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "country": self.country,
            "source": self.source,
            "url": self.url,
            "posted_date": self.posted_date.isoformat() if isinstance(self.posted_date, (date, datetime)) else self.posted_date,
            "match_score": self.match_score,
            "match_reasons": list(self.match_reasons),
        }


@dataclass
class DailyReport:
    report_date: str
    timezone: str
    generated_at: datetime
    search_window_days: int = 14
    jobs: list[DailyReportJob] = field(default_factory=list)
    total_jobs: int = 0

    def __post_init__(self) -> None:
        self.total_jobs = len(self.jobs)

    def as_dict(self) -> dict[str, object]:
        return {
            "report_date": self.report_date,
            "generated_at": self.generated_at.isoformat(),
            "timezone": self.timezone,
            "search_window_days": self.search_window_days,
            "jobs": [job.as_dict() for job in self.jobs],
            "total_jobs": self.total_jobs,
        }


DailyJobReport = DailyReport
