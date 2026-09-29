from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.nationalevacaturebank")


class NationaleVacaturebankCollector(BaseCollector):
    """Safe-disabled collector for Nationale Vacaturebank.

    This adapter remains disabled until a public, documented, and permitted
    API or feed is available. No unauthorized scraping or access bypass is
    attempted.
    """

    source_name = "nationalevacaturebank.nl"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.nationalevacaturebank.nl",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("NATIONALEVACATUREBANK_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; requires a documented, permitted public API or feed before live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "No verified public API or feed was identified for this project, so automated collection remains disabled.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Nationale Vacaturebank adapter is disabled because no verified public API or feed is configured.")
            return []

        logger.warning("Nationale Vacaturebank is enabled but no permitted public access mechanism is configured; refusing automated collection.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Netherlands"
        job.source = self.source_name
        return job
