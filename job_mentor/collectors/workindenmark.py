from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.workindenmark")


class WorkindenmarkCollector(BaseCollector):
    """Safe-disabled collector for Workindenmark.

    The current official Workindenmark site directs users to a Jobnet-hosted
    vacancy search experience and presents the system as a public information and
    guidance portal rather than a developer-oriented public job API. No verified
    public feed or API contract is accepted for this project.
    """

    source_name = "workindenmark.dk"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.workindenmark.dk",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("WORKINDENMARK_ENABLED", "false").strip().lower()
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
            "reason": "Workindenmark is treated as a public information portal; no verified public vacancy-search API or feed is accepted for automated collection in this project.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Workindenmark adapter is disabled because no documented public vacancy-search API or feed is configured.")
            return []

        logger.warning("Workindenmark is enabled but no documented public retrieval contract is configured; refusing to scrape or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Denmark"
        job.source = self.source_name
        return job
