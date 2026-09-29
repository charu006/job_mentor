from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.jobs_lu")


class JobsLuCollector(BaseCollector):
    """Safe-disabled collector for Jobs.lu.

    Jobs.lu indicates use for individuals and explicitly prohibits development of
    other services. No verified documented public vacancy API/feed was identified
    for this project. The project does not treat public access as permission to
    scrape HTML or reverse-engineer non-public interfaces.
    """

    source_name = "jobs.lu"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.jobs.lu",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBS_LU_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Jobs.lu terms are intended for individual job searching and prohibit use for developing other services; no verified public vacancy-search API/feed for this project was identified.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "Jobs.lu is explicitly enabled only with a documented and permitted public retrieval contract.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Jobs.lu adapter is disabled because the current terms do not authorize systematic automated retrieval for this project.")
            return []

        logger.warning("Jobs.lu is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape HTML or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Luxembourg"
        job.source = self.source_name
        return job
