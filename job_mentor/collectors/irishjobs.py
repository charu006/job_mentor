from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.irishjobs")


class IrishJobsCollector(BaseCollector):
    """Safe-disabled collector for IrishJobs.ie.

    IrishJobs is operated by The Stepstone Group Ireland Recruit Limited and its
    current terms restrict removing website content by competitive means. The
    project does not use scraping, crawlers, or any bypass mechanism against this
    site without a documented public API or partner retrieval contract.
    """

    source_name = "irishjobs.ie"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.irishjobs.ie",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("IRISHJOBS_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented public partner API or feed contract should be used for live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "IrishJobs.ie terms expressly restrict removing website content by competitive means; this project does not scrape or bypass the site and keeps the portal disabled.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("IrishJobs adapter is disabled because no documented partner API or permitted public retrieval mechanism is configured.")
            return []

        logger.warning("IrishJobs is enabled but no documented public retrieval contract is configured; refusing to scrape or override site access controls.")
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
