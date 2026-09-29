from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.pracuj")


class PracujCollector(BaseCollector):
    """Safe-disabled collector for Pracuj.pl.

    Pracuj.pl currently exposes candidate-facing public job-search pages, but no
    documented public vacancy-search API/feed has been verified as authorized for
    this project. Public visibility alone is not treated as permission to build a
    systematic automated collection pipeline or scrape HTML.
    """

    source_name = "pracuj.pl"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.pracuj.pl",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("PRACUJ_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Pracuj.pl is intentionally disabled because no verified public job-search API/feed authorized for automated collection was identified; public job-search pages are not treated as permission to scrape or bypass access controls.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "Pracuj.pl is explicitly enabled, but only with an officially documented and permitted retrieval interface should live collection be attempted.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Pracuj.pl adapter is disabled because no authorized public API/feed contract has been verified for this project.")
            return []

        logger.warning("Pracuj.pl is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape HTML or bypass site access controls.")
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
