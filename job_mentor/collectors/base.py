from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors")


class BaseCollector(ABC):
    """Common interface implemented by all portal collectors."""

    source_name = "unknown"

    def __init__(self, search_terms: list[str] | None = None):
        self.search_terms = search_terms or []

    @abstractmethod
    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        raise NotImplementedError

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        if not isinstance(raw_job, dict):
            return None

        title = raw_job.get("title") or raw_job.get("job_title") or raw_job.get("name")
        company = raw_job.get("company") or raw_job.get("employer") or raw_job.get("organization")
        location = raw_job.get("location") or raw_job.get("city") or raw_job.get("place")
        description = raw_job.get("description") or raw_job.get("summary") or raw_job.get("text")
        url = raw_job.get("url") or raw_job.get("job_url") or raw_job.get("link")
        source_job_id = raw_job.get("source_job_id") or raw_job.get("id") or raw_job.get("job_id")
        posted_date = raw_job.get("posted_date") or raw_job.get("published_at") or raw_job.get("date")

        if not title:
            return None

        return Job(
            title=str(title),
            company=str(company) if company else None,
            location=str(location) if location else None,
            country="Germany",
            source=self.source_name,
            source_job_id=str(source_job_id) if source_job_id else None,
            url=str(url) if url else None,
            description=str(description) if description else None,
            posted_date=posted_date,
        )

    def collect_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        return self.search_jobs(terms=terms, **kwargs)
