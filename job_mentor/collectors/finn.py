from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.finn")


class FinnCollector(BaseCollector):
    """Safe-disabled collector for FINN.no.

    The current public interface is not treated as a verified, permitted automated
    retrieval contract for this project. The adapter remains disabled and does not
    scrape HTML or bypass access restrictions.
    """

    source_name = "finn.no"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.finn.no/job",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("FINN_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "FINN.no is intentionally disabled in this project because no verified public API/feed contract or explicit permission for automated retrieval was identified.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "FINN.no is explicitly enabled; only with a documented public retrieval interface would live collection be attempted.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("FINN.no adapter is disabled because the current public interface does not provide a documented automated retrieval contract for this project.")
            return []

        logger.warning("FINN.no is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Finland"
        job.source = self.source_name
        return job
