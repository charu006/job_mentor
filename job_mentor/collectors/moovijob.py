from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.moovijob")


class MoovijobCollector(BaseCollector):
    """Safe-disabled collector for Moovijob.

    The official terms allow job search and alerts for users but prohibit illicit
    access and actions that compromise site operation. No verified public
    vacancy-search API/feed is documented and authorized for this project.
    """

    source_name = "moovijob.com"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.moovijob.com",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("MOOVIJOB_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Moovijob terms prohibit illicit access and site-compromising automation; no verified public vacancy-search API/feed authorized for this project was identified.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "Moovijob is explicitly enabled only with a documented and permitted public retrieval contract.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Moovijob adapter is disabled because the current terms do not authorize systematic automated retrieval for this project.")
            return []

        logger.warning("Moovijob is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape HTML or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Luxembourg"
        job.source = self.source_name
        return job
