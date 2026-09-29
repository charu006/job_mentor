from __future__ import annotations

import logging
import os
from typing import Any

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.euraxess")


class EuraxessCollector(BaseCollector):
    """Safe-disabled EURAXESS collector.

    The current official EURAXESS domain is https://euraxess.ec.europa.eu/.
    Legacy domains such as euraxess.eu and thenetwork.euraxesss.org are not
    treated as the active public retrieval network for the project. No public
    vacancy-search API/feed contract was identified that authorizes automated
    retrieval for this project.
    """

    source_name = "euraxess.ec.europa.eu"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://euraxess.ec.europa.eu",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = self._normalize_base_url(base_url)
        self.enabled = self._resolve_enabled(enabled)

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        value = (base_url or "https://euraxess.ec.europa.eu").strip().rstrip("/")
        normalized = value.lower()
        legacy_values = {
            "https://euraxess.eu",
            "http://euraxess.eu",
            "https://thenetwork.euraxesss.org",
            "http://thenetwork.euraxesss.org",
        }
        if normalized in legacy_values:
            return "https://euraxess.ec.europa.eu"
        return value

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("EURAXESS_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Legacy EURAXESS domains are not the official current portal, and the current official domain is https://euraxess.ec.europa.eu. No public vacancy-search API/feed was identified that authorizes automated retrieval for this project.",
            }
        return {
            "portal": self.source_name,
            "status": "enabled",
            "reason": "EURAXESS is enabled only when a documented public retrieval contract is explicitly configured and authorized for project use.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("EURAXESS collector is disabled because the active official portal does not expose a documented vacancy retrieval API/feed for this project.")
            return []

        logger.warning("EURAXESS is enabled only with a documented public retrieval contract; no supported public collection method was configured for this project.")
        return []

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        job.country = "EU"
        job.source = self.source_name
        return job
