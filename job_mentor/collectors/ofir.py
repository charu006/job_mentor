from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.ofir")


class OfirCollector(BaseCollector):
    """Safe-disabled collector for Ofir.dk.

    The current official Ofir home page is closed and redirects to Jobindex.
    There is no verified public API or feed mechanism in the current official
    deployment that this project can use without violating access controls.
    """

    source_name = "ofir.dk"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.ofir.dk",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("OFIR_ENABLED", "false").strip().lower()
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
            "reason": "Ofir.dk is currently closed and no supported public vacancy retrieval API or feed is available. Automated collection remains disabled.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Ofir adapter is disabled because the official portal is closed and no public retrieval interface is verified.")
            return []

        logger.warning("Ofir is enabled but no documented public API or feed is configured; refusing to scrape or bypass access controls.")
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
