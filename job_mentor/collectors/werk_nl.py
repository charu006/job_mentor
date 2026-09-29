from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.werk_nl")


class WerkNLCollector(BaseCollector):
    """Safe-disabled collector for werk.nl.

    Current public terms and access guidance prohibit automated extraction,
    scraping, bots, or similar collection methods. This adapter intentionally
    does not bypass that restriction and remains disabled unless an explicit,
    permitted public API or feed is later documented.
    """

    source_name = "werk.nl"

    def __init__(self, search_terms: list[str] | None = None, enabled: bool | None = None, base_url: str = "https://www.werk.nl"):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("WERK_NL_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; this project does not currently authorize automation for werk.nl under the public terms.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "Automated collection is disabled because werk.nl's current public terms prohibit scraper/bot-style access to vacancy data.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("werk.nl adapter is disabled because automated collection is prohibited by the public access terms.")
            return []

        logger.warning("werk.nl is enabled but no permitted public API or feed is configured; refusing to scrape or circumvent access controls.")
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
