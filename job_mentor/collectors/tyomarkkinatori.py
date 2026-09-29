from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.tyomarkkinatori")


class TyomarkkinatoriCollector(BaseCollector):
    """Safe-disabled collector for Työmarkkinatori.

    The current official site documents a retrieval interface for approved
    organisational clients, but that interface requires activation, business-ID
    validation, KEHA eligibility checks and credentials. This project does not
    have separate organisational approval or credentials, so this collector stays
    disabled and does not attempt scraping as a replacement.
    """

    source_name = "tyomarkkinatori.fi"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://tyomarkkinatori.fi",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("TYOMARKKINATORI_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if self.enabled:
            return {
                "portal": self.source_name,
                "status": "enabled",
                "reason": "Explicitly enabled; only a documented official retrieval API with valid organisational activation and credentials should be used.",
            }
        return {
            "portal": self.source_name,
            "status": "disabled",
            "reason": "The official Työmarkkinatori retrieval interface requires activation, business-ID validation, KEHA eligibility checks and credentials; no organisational approval or credentials are configured for this project.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Työmarkkinatori adapter is disabled because the official retrieval API requires activation and credentials that this project does not have.")
            return []

        logger.warning("Työmarkkinatori is explicitly enabled but no approved organisational retrieval API credentials are configured; refusing to scrape or bypass access controls.")
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
