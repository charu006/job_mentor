from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.jobbsafari")


class JobbSafariCollector(BaseCollector):
    """Safe-disabled collector for JobbSafari.

    The current terms permit ordinary links to publicly available pages but
    prohibit systematic copying, scraping, and competing or substantially similar
    service use without explicit written approval. This project does not bypass
    those restrictions and does not scrape HTML from the site.
    """

    source_name = "jobbsafari.se"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://jobbsafari.se",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBBSAFARI_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "JobbSafari current terms prohibit systematic copying/scraping and competing or substantially similar use without explicit written approval; no verified public retrieval API or feed intended for this project was identified.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "JobbSafari is explicitly enabled, but only with a documented public and permitted retrieval contract should live collection be attempted.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("JobbSafari adapter is disabled because the current terms prohibit scraping and competing use without explicit written approval.")
            return []

        logger.warning("JobbSafari is explicitly enabled but no documented public retrieval contract is configured; refusing to scrape HTML or bypass access controls.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Sweden"
        job.source = self.source_name
        return job
