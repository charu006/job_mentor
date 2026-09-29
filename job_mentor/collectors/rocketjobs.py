from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.rocketjobs")


class RocketJobsCollector(BaseCollector):
    """Safe-disabled collector for RocketJobs.pl.

    The current official terms forbid copying, downloading, and distributing job
    application content and database material without prior written permission.
    This project does not treat browser visibility as permission to scrape or use
    undocumented APIs to copy protected board data.
    """

    source_name = "rocketjobs.pl"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://rocketjobs.pl",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("ROCKETJOBS_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "RocketJobs.pl terms prohibit copying, downloading, and redistributing application content and database material without prior written permission; no documented public API/feed for this project was identified.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "RocketJobs.pl is explicitly enabled, but only with a documented and explicitly permitted public retrieval mechanism should live collection be attempted.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("RocketJobs.pl adapter is disabled because the current terms prohibit copying/downloading protected application content or database material without prior written permission.")
            return []

        logger.warning("RocketJobs.pl is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape HTML or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Poland"
        job.source = self.source_name
        return job
