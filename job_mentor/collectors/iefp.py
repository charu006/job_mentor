from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.iefp")


class IefpCollector(BaseCollector):
    """Safe-disabled collector for emprego.iefp.pt.

    The current IEFP public portal exposes vacancy information via a user-facing
    experience but no current public API, feed, or explicitly permitted machine-
    readable interface was identified for automated retrieval in this project.
    """

    source_name = "iefp.pt"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://emprego.iefp.pt",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("IEFP_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented public vacancy API or feed contract should be used for live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "IEFP does not provide a documented public vacancy-search API or feed for automated collection in this project, and ordinary public visibility is not treated as permission to scrape.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("IEFP adapter is disabled because no documented public vacancy API or permitted feed was identified.")
            return []

        logger.warning("IEFP is enabled but no authorized public retrieval contract is configured; refusing to scrape or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Portugal"
        job.source = self.source_name
        return job
