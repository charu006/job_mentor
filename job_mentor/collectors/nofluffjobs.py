from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.nofluffjobs")


class NoFluffJobsCollector(BaseCollector):
    """Safe-disabled collector for No Fluff Jobs.

    The official No Fluff Jobs terms expressly prohibit downloading or reusing
    job-board material, including individual job advertisements, unless a separate
    explicit permission or API/feed contract is provided. This project does not
    bypass those restrictions through browser automation, hidden endpoints, or
    other scraping workarounds.
    """

    source_name = "nofluffjobs.com"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://nofluffjobs.com",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("NOFLUFFJOBS_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "No Fluff Jobs terms prohibit downloading/reusing job-board data and individual advertisements without explicit permission; this project does not bypass those restrictions or use undocumented APIs/scraping workarounds.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "No Fluff Jobs is explicitly enabled, but only via a documented and explicitly permitted public retrieval contract should live collection be attempted.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("No Fluff Jobs adapter is disabled because the current terms prohibit downloading or reusing board data without explicit permission.")
            return []

        logger.warning("No Fluff Jobs is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape, use undocumented APIs, or bypass access controls.")
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
