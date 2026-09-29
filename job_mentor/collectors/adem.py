from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.adem")


class AdemCollector(BaseCollector):
    """Safe-disabled collector for ADEM / adem.public.lu.

    The current official ADEM materials indicate a public JobBoard, but no verified
    official public vacancy-search API/feed is documented and permitted for this
    project. Public visibility alone is not treated as permission to scrape,
    reverse-engineer hidden frontend endpoints, or automate against the site.
    """

    source_name = "adem.public.lu"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://adem.public.lu",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("ADEM_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "ADEM public vacancies are not treated as a verified public vacancy-search API/feed for this project; public visibility does not authorize scraping or bypassing access controls.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "ADEM is explicitly enabled only with a documented and permitted public retrieval contract.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("ADEM adapter is disabled because no verified public vacancy-search API/feed was identified for this project.")
            return []

        logger.warning("ADEM is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape or bypass access controls.")
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
