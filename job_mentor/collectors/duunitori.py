from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.duunitori")


class DuunitoriCollector(BaseCollector):
    """Safe-disabled collector for Duunitori.

    Duunitori documents recruitment-related XML/RSS/JSON integrations for job
    advertisements, but that does not establish a public vacancy-search feed or
    retrieval interface for this project. Without a clearly documented, public and
    permitted automated feed/API, this collector remains disabled and does not
    scrape search result pages.
    """

    source_name = "duunitori.fi"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://duunitori.fi",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("DUUNITORI_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented public XML/RSS/JSON feed or partner API with permitted access should be used.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "Duunitori does not provide a clearly documented public vacancy-search feed or retrieval API for automated collection in this project, and public advertiser documentation is not treated as permission to scrape candidate pages.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Duunitori adapter is disabled because there is no clearly documented public vacancy feed or permitted automated retrieval interface for this project.")
            return []

        logger.warning("Duunitori is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape search result pages or bypass access controls.")
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
