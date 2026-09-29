from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from job_mentor.models.job import Job


@dataclass
class DailyJobReport:
    report_date: str
    timezone: str
    generated_at: datetime
    jobs: list[Job] = field(default_factory=list)
    total_jobs: int = 0

    def __post_init__(self) -> None:
        self.total_jobs = len(self.jobs)
