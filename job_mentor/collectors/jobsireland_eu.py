from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.jobsireland_eu")


class JobsIrelandEuCollector(BaseCollector):
    """Safe-disabled jobsireland.eu collector.

    This is not the same service as jobsireland.ie. The project does not assume
    that a public page is an authorized automated retrieval source. No verified
    public vacancy-search API or feed contract for jobsireland.eu was identified.
    """

    source_name = "jobsireland.eu"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://jobsireland.eu",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/") if base_url else "https://jobsireland.eu"
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBSIRELAND_EU_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "jobsireland.eu is not the same service as jobsireland.ie and no verified public vacancy-search API/feed or explicit authorization was identified for this project. This domain is treated as a separate legacy or inactive source unless an explicit public retrieval contract is documented.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "jobsireland.eu is enabled only when an official public retrieval contract is explicitly configured and authorized for project use.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("jobsireland.eu collector is disabled because no documented public retrieval contract for automated collection was identified.")
            return []

        logger.warning("jobsireland.eu is enabled only with a documented public retrieval contract; no supported public collection method was configured for this project.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        job.country = "Ireland"
        job.source = self.source_name
        return job
