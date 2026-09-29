from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.jobup_ch")


class JobUpCHCollector(BaseCollector):
    """Safe-disabled collector for jobup.ch.

    This project does not bypass the public platform's job-seeker terms or
    attempt automated access without a documented and authorized public API/feed.
    """

    source_name = "jobup.ch"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.jobup.ch",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBUP_CH_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; this project requires a documented, permitted public vacancy API or feed before any live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "jobup.ch is intentionally disabled because there is no verified public retrieval API/feed for this project and scraping is not authorized.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("jobup.ch adapter is disabled because automated collection is not authorized.")
            return []

        logger.warning("jobup.ch is enabled but no permitted public API or feed is configured; refusing to scrape or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Switzerland"
        job.source = self.source_name
        return job
