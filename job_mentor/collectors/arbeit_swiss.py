from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.arbeit_swiss")


class ArbeitSwissCollector(BaseCollector):
    """Safe-disabled collector for arbeit.swiss.

    The current public documentation presents the Job-Room interface as an
    employer-facing publishing and job-registration mechanism, not a public
    vacancy-search API for this project. We do not use employer publication APIs
    to read jobs without a valid, documented read/search contract.
    """

    source_name = "arbeit.swiss"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.arbeit.swiss",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("ARBEIT_SWISS_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; this project requires a documented public vacancy retrieval API or feed before any live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "The public Job-Room interface is not treated as a public vacancy-search API for this project; automated collection remains disabled.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("arbeit.swiss adapter is disabled because no permitted public vacancy-search API was identified.")
            return []

        logger.warning("arbeit.swiss is enabled but no documented read/search contract is configured for this project; refusing to use employer publishing APIs for job retrieval.")
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
