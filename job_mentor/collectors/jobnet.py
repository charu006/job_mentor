from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.jobnet")


class JobNetCollector(BaseCollector):
    """Safe-disabled collector for Jobnet.dk.

    Jobnet exposes a public candidate-facing search interface, but the current
    official employer-side material and access flows are controlled through
    employer / JobAG / MitID Erhverv authentication. This project does not use
    authenticated employer APIs or any undocumented public job retrieval path.
    """

    source_name = "jobnet.dk"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://jobnet.dk",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBNET_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented, permitted public vacancy API/feed should be used for live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "Jobnet exposes a public job-search user experience, but no documented public vacancy-search API or feed is currently accepted for this project. Automated collection remains disabled.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Jobnet adapter is disabled because no documented public vacancy-search API or feed is configured.")
            return []

        logger.warning("Jobnet is enabled but no verified public retrieval contract has been configured; refusing to use employer-only interfaces or scraping.")
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
