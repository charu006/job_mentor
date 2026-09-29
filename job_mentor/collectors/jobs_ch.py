from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.jobs_ch")


class JobsCHCollector(BaseCollector):
    """Safe-disabled collector for jobs.ch.

    JobCloud's public employer-facing recruiting tools and terms emphasize
    advertiser, employer, and candidate-management products. The project does not
    use crawlers, scripts, or unauthorized automated access against JobCloud sites.
    """

    source_name = "jobs.ch"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.jobs.ch",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBS_CH_ENABLED", "false").strip().lower()
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
            "reason": "jobs.ch is intentionally disabled because public access and terms do not authorize scraping or automated data extraction for this project.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("jobs.ch adapter is disabled because public automated access is not authorized.")
            return []

        logger.warning("jobs.ch is enabled but no permitted public API or feed is configured; refusing to scrape or bypass access controls.")
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
