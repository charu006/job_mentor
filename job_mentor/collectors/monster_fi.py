from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.monster_fi")


class MonsterFiCollector(BaseCollector):
    """Safe-disabled collector for Monster.fi.

    The current Finnish service is effectively a rebranded Jobly/Alma surface.
    The project does not treat monster.fi as an independent active portal without a
    documented public job feed/API or explicit permission for automated retrieval.
    Without that contract, the collector remains disabled and does not scrape
    Jobly/Monster pages.
    """

    source_name = "monster.fi"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.monster.fi",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("MONSTER_FI_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only with a documented public partner API, official feed, or other authorized interface should live collection be attempted.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "Monster.fi has rebranded to Jobly/Alma in current official service flows; this project does not treat it as an independent active portal without a documented public retrieval contract, and it does not scrape or bypass access controls.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Monster.fi adapter is disabled because the current service is a rebranded Jobly/Alma experience without a documented public retrieval API/feed for this project.")
            return []

        logger.warning("Monster.fi is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape Jobly/Monster pages or bypass access management.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Finland"
        job.source = self.source_name
        return job
