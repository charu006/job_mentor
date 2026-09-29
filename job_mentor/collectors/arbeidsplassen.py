from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job

logger = logging.getLogger("job_mentor.collectors.arbeidsplassen")


class ArbeidsplassenCollector(BaseCollector):
    """Official public API collector for NAV / Arbeidsplassen.

    This project uses the public job-ad API surface exposed by NAV rather than
    scraping the browser HTML interface. The collector remains enabled by default
    because the public interface is documented and intended for automated access.
    """

    source_name = "arbeidsplassen.nav.no"
    default_max_requests = 10

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        api_base_url: str | None = None,
        base_url: str = "https://arbeidsplassen.nav.no",
        search_url: str | None = None,
        max_requests: int | None = None,
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.api_base_url = (api_base_url or os.getenv("ARBEIDSPLASSEN_API_BASE_URL", self.base_url)).rstrip("/")
        self.search_url = (search_url or os.getenv("ARBEIDSPLASSEN_SEARCH_URL", f"{self.api_base_url}/public-ads-api")).rstrip("/")
        self.enabled = self._resolve_enabled(enabled)
        self.max_requests = self._resolve_max_requests(max_requests)

    def _resolve_max_requests(self, override: int | None) -> int:
        if override is not None:
            return max(1, int(override))
        raw_value = os.getenv("ARBEIDSPLASSEN_MAX_REQUESTS", str(self.default_max_requests)).strip()
        try:
            return max(1, int(raw_value))
        except ValueError:
            logger.warning("Invalid ARBEIDSPLASSEN_MAX_REQUESTS value %r; using default %s.", raw_value, self.default_max_requests)
            return self.default_max_requests

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("ARBEIDSPLASSEN_ENABLED", "true").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Arbeidsplassen remains disabled by configuration until explicitly enabled.",
            }
        return {
            "portal": self.source_name,
            "status": "active",
            "reason": "Official public NAV/Arbeidsplassen JSON API access is configured and enabled for this project.",
        }

    def _fetch_search_page(self, q: str = "polymer", offset: int = 0, limit: int = 10) -> dict[str, Any]:
        params = {
            "q": q,
            "offset": offset,
            "limit": limit,
            "sort": "published",
        }
        request = Request(
            f"{self.search_url}?{urlencode(params)}",
            headers={
                "Accept": "application/json",
                "User-Agent": "JobMentor/0.1",
            },
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = response.read().decode("utf-8", errors="ignore")
                if not payload:
                    return {}
                return json.loads(payload)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            logger.warning("NAV/Arbeidsplassen API request failed for query %s at offset %s: %s", q, offset, exc)
            raise RuntimeError(str(exc)) from exc

    def _extract_jobs(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        for key in ("ads", "hits", "results", "jobs"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return []

    def search_jobs(self, terms: list[str] | None = None, limit: int = 10, max_pages: int = 2, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Arbeidsplassen adapter is disabled by configuration; public API collection is off until explicitly enabled.")
            return []

        query_terms = list(terms or self.search_terms or [])
        if not query_terms:
            query_terms = [
                "polymer",
                "elastomer",
                "rubber technology",
                "material development",
                "gummi",
                "materialutvikling",
            ]

        jobs: list[Job] = []
        seen_ids: set[str] = set()
        requests_made = 0

        for term in query_terms:
            if not term or not isinstance(term, str):
                continue
            if requests_made >= self.max_requests:
                logger.info("Arbeidsplassen request budget exhausted after %s API calls; stopping before additional requests.", requests_made)
                break

            offset = 0
            for _ in range(max_pages):
                if requests_made >= self.max_requests:
                    logger.info("Arbeidsplassen request budget exhausted after %s API calls; stopping before the next HTTP request.", requests_made)
                    break

                requests_made += 1
                try:
                    payload = self._fetch_search_page(q=term, offset=offset, limit=limit)
                except Exception as exc:
                    logger.warning("Skipping Arbeidsplassen query %s after API error: %s", term, exc)
                    break

                hits = self._extract_jobs(payload)
                if not hits:
                    break

                for raw_job in hits:
                    normalized = self.normalize_raw_job(raw_job)
                    if normalized is None:
                        continue
                    source_id = normalized.source_job_id or normalized.url or normalized.title
                    if source_id in seen_ids:
                        continue
                    seen_ids.add(str(source_id))
                    normalized.country = "Norway"
                    normalized.source = self.source_name
                    jobs.append(normalized)

                if len(hits) < limit:
                    break
                offset += len(hits)

                if requests_made >= self.max_requests:
                    logger.info("Arbeidsplassen request budget reached (%s/%s); stopping before the next page request.", requests_made, self.max_requests)
                    break

        return jobs

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        if not isinstance(raw_job, dict):
            return None

        title = raw_job.get("title") or raw_job.get("headline") or raw_job.get("job_title") or raw_job.get("name")
        company = raw_job.get("company") or raw_job.get("employer") or raw_job.get("organization")
        if isinstance(company, dict):
            company = company.get("name") or company.get("organization_name")

        location = raw_job.get("location") or raw_job.get("city") or raw_job.get("place")
        if isinstance(location, dict):
            location = location.get("city") or location.get("municipality") or location.get("country") or location.get("name")

        description = raw_job.get("description") or raw_job.get("summary") or raw_job.get("text")
        url = raw_job.get("link") or raw_job.get("url") or raw_job.get("job_url") or raw_job.get("webpage_url")
        source_job_id = raw_job.get("id") or raw_job.get("source_job_id") or raw_job.get("job_id")
        posted_date = raw_job.get("published") or raw_job.get("published_at") or raw_job.get("date") or raw_job.get("created")

        if not title:
            return None

        job = Job(
            title=str(title),
            company=str(company) if company else None,
            location=str(location) if location else None,
            country="Norway",
            source=self.source_name,
            source_job_id=str(source_job_id) if source_job_id else None,
            url=str(url) if url else None,
            description=str(description) if description else None,
            posted_date=posted_date,
        )
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        return job
