from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.academic_work")


class AcademicWorkCollector(BaseCollector):
    """Safe-disabled collector for Academic Work Sweden.

    The public job-search service exists, but no clearly documented public
    vacancy API or feed suitable for automated collection by this project was
    identified. The project does not treat public website visibility as a
    permission to scrape or bypass access controls.
    """

    source_name = "academicwork.se"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.academicwork.se",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("ACADEMICWORK_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Academic Work Sweden does not expose a clearly documented public jobs API or feed intended for this project, and public website access is not treated as permission to scrape or bypass restrictions.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "Academic Work Sweden is explicitly enabled, but only a documented public retrieval contract should be used.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Academic Work adapter is disabled because no verified public API or feed was identified for automated retrieval.")
            return []

        logger.warning("Academic Work is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape HTML or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Sweden"
        job.source = self.source_name
        return job
