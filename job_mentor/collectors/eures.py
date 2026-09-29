from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.eures")


class EuresCollector(BaseCollector):
    """Safe-disabled EURES collector.

    Europass Find Jobs is a public interface over the EURES labour-mobility
    portal. This project does not assume that a public website front end is an
    authorized automated retrieval service. No verified public vacancy-search
    API or feed contract for this project was identified.
    """

    source_name = "eures.europa.eu"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://eures.europa.eu",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/") if base_url else "https://eures.europa.eu"
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("EURES_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "The Europass Find Jobs experience is served by the EURES labour-mobility portal, but no current documented public vacancy-search API/feed was identified that authorizes automated retrieval for this project. The public front end is not treated as an authorized automated collection surface.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "EURES is enabled only when a documented public retrieval contract is explicitly configured and authorized for project use.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("EURES collector is disabled because the current official public interface does not provide an authorized vacancy-search API/feed for this project.")
            return []

        logger.warning("EURES is enabled only with a documented public retrieval contract; no automated public feed or API was configured for this project.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        job.country = "EU"
        job.source = self.source_name
        return job
