from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.recruitireland")


class RecruitIrelandCollector(BaseCollector):
    """Safe-disabled collector for recruitireland.com.

    The site permits viewing download of public information within the intended
    use of the platform, but does not authorize automated scraping or actions that
    interfere with operation or bypass controls. Without a documented public API,
    feed, or explicitly permitted automated interface, the project keeps this
    collector disabled.
    """

    source_name = "recruitireland.com"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.recruitireland.com",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("RECRUITIRELAND_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented, permitted public vacancy API or feed should be used for live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "RecruitIreland terms do not authorize automated scraping or bypassing access controls; without a documented public API/feed, the project keeps this collector disabled.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("RecruitIreland adapter is disabled because no documented public retrieval interface is configured.")
            return []

        logger.warning("RecruitIreland is enabled but no documented public API or feed is configured; refusing to scrape or bypass usage restrictions.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Ireland"
        job.source = self.source_name
        return job
