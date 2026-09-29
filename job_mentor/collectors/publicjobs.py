from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.publicjobs")


class PublicJobsCollector(BaseCollector):
    """Safe-disabled collector for publicjobs.ie.

    The current official terms state the site is for personal, non-commercial use
    and restrict copying, reproduction, and public distribution of site content.
    The project does not treat ordinary public visibility as permission to scrape,
    crawl, or reproduce site data without a documented automated interface.
    """

    source_name = "publicjobs.ie"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.publicjobs.ie",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("PUBLICJOBS_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented, permitted public vacancy API or feed should be used for live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "publicjobs.ie terms restrict copying and reproduction for personal, non-commercial use; the project does not treat ordinary public visibility as permission to automate collection.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("PublicJobs adapter is disabled because no permitted public API or feed is configured.")
            return []

        logger.warning("PublicJobs is enabled but no documented public retrieval contract is configured; refusing to scrape or bypass website access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Ireland"
        job.source = self.source_name
        return job
