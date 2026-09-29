from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.stepstone")


class StepStoneCollector(BaseCollector):
    """Disabled-safe adapter for StepStone.

    StepStone is not currently automated in this project because the public
    portal does not provide a verified, permitted API or feed for the required
    use case without explicit authorization. This adapter fails gracefully and
    keeps the rest of the pipeline running.
    """

    source_name = "stepstone.de"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.stepstone.com",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("STEPSTONE_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; requires a verified, permitted StepStone API or feed contract before live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "StepStone requires explicit authorization or a documented public API; no verified credentials or permitted automated access exist in this project.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info(
                "StepStone adapter is disabled; no permitted public API or credentials are configured for %s.",
                self.source_name,
            )
            return []

        logger.warning(
            "StepStone is enabled but no verified, authorized API access is configured for this local project. "
            "Skipping live collection to avoid unauthorized scraping."
        )
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Germany"
        job.source = self.source_name
        return job
