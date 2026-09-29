from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job
from job_mentor.network import urlopen_with_reliable_ssl as urlopen

logger = logging.getLogger("job_mentor.collectors.jobdigger")


class JobDiggerCollector(BaseCollector):
    """JobDigger collector using the documented public API.*

    The API is keyed and must be configured with a real API key in the
    environment. No key is hard-coded in the repository. The collector remains
    disabled if the feature is not explicitly enabled or the key is missing.
    """

    source_name = "jobdigger.nl"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        api_key: str | None = None,
        base_url: str = "https://api.jobdigger.com",
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.enabled = self._resolve_enabled(enabled)
        self.api_key = (api_key or os.getenv("JOBDIGGER_API_KEY", "")).strip()

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBDIGGER_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    @property
    def is_configured(self) -> bool:
        return self.enabled and bool(self.api_key)

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "JobDigger collection is disabled by configuration and remains off until explicitly enabled.",
            }
        if not self.api_key:
            return {
                "portal": self.source_name,
                "status": "api-key-required",
                "reason": "JobDigger is enabled but no JOBDIGGER_API_KEY is configured. The collector stays unavailable without credentials.",
            }
        return {
            "portal": self.source_name,
            "status": "active",
            "reason": "JobDigger API access is configured and permitted for this project.",
        }

    def _request_json(self, payload: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        if not self.is_configured:
            return {}

        url = f"{self.base_url}/v2/search"
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Key": self.api_key,
            "User-Agent": "JobMentor/0.1 (+https://github.com/your-org/job_mentor)",
        }

        request = Request(url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=20) as response:
                raw = response.read().decode("utf-8", errors="ignore")
                if not raw:
                    return {}
                return json.loads(raw)
        except HTTPError as exc:
            logger.warning("JobDigger API returned HTTP %s for search request: %s", exc.code, exc.reason)
            return {}
        except (URLError, TimeoutError, ValueError) as exc:
            logger.warning("JobDigger API request failed: %s", exc)
            return {}

    def _extract_jobs(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("jobs", "results", "data", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            if isinstance(payload.get("job"), dict):
                return [payload["job"]]
        return []

    def search_jobs(self, terms: list[str] | None = None, days: int = 14, **kwargs) -> list[Job]:
        if not self.is_configured:
            logger.info("JobDigger adapter is disabled or not configured: missing JOBDIGGER_API_KEY or JOBDIGGER_ENABLED flag.")
            return []

        active_terms = terms or self.search_terms
        if not active_terms:
            active_terms = ["elastomer", "polymer", "rubber technology"]

        jobs: list[Job] = []
        for term in active_terms:
            payload = self._request_json({
                "query": term,
                "location": "Netherlands",
                "page": 1,
                "pageSize": 10,
            })
            for raw_job in self._extract_jobs(payload):
                normalized = self.normalize_raw_job(raw_job)
                if normalized is None:
                    continue
                normalized.country = "Netherlands"
                normalized.source = self.source_name
                if normalized.posted_date is not None:
                    jobs.append(normalized)
        return jobs

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        if not isinstance(raw_job, dict):
            return None

        title = raw_job.get("title") or raw_job.get("job_title") or raw_job.get("name")
        company = raw_job.get("company") or raw_job.get("employer") or raw_job.get("organization")
        location = raw_job.get("location") or raw_job.get("city") or raw_job.get("place") or raw_job.get("country")
        description = raw_job.get("description") or raw_job.get("summary") or raw_job.get("text")
        source_job_id = raw_job.get("reference") or raw_job.get("job_reference") or raw_job.get("id") or raw_job.get("job_id")
        url = raw_job.get("url") or raw_job.get("job_url") or raw_job.get("link")
        posted_date = raw_job.get("posted_date") or raw_job.get("published_at") or raw_job.get("date")

        if not title:
            return None

        job = Job(
            title=str(title),
            company=str(company) if company else None,
            location=str(location) if location else None,
            country="Netherlands",
            source=self.source_name,
            source_job_id=str(source_job_id) if source_job_id else None,
            url=str(url) if url else None,
            description=str(description) if description else None,
            posted_date=posted_date,
        )
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        return job
