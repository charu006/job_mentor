from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.beebez")


class BeebezCollector(BaseCollector):
    """Safe-disabled collector for beebez.pt.

    The requested domain does not appear to be a current job portal; the current
    public Beebez site appears to be a consumer retail domain and not an active
    public employment portal. Without a documented public jobs API or feed, this
    project keeps the adapter disabled and does not substitute another portal.
    """

    source_name = "beebez.pt"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://beebez.pt",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("BEEBEZ_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented public recruitment API, feed, or partner interface should be used for live collection.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "The requested beebez.pt domain does not appear to be an active public job portal and no documented public jobs API/feed is accepted for automated retrieval in this project.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Beebez adapter is disabled because the current domain is not an active public jobs portal and no official retrieval interface was identified.")
            return []

        logger.warning("Beebez is enabled but no documented public job API/feed is configured; refusing to scrape or substitute another portal without verified documentation.")
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
