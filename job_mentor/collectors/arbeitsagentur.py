from __future__ import annotations

import json
import logging
from urllib.parse import quote
from urllib.request import Request, urlopen

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job
from job_mentor.utils.dates import is_within_search_window

logger = logging.getLogger("job_mentor.collectors.arbeitsagentur")


class ArbeitsagenturCollector(BaseCollector):
    """Collector for the German Federal Employment Agency portal."""

    source_name = "jobs.arbeitsagentur.de"

    def __init__(self, search_terms: list[str] | None = None, base_url: str = "https://jobs.arbeitsagentur.de"):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")

    def build_search_url(self, term: str) -> str:
        term_value = quote(term.strip())
        return f"{self.base_url}/suche?term={term_value}&page=1"

    def fetch_raw_jobs(self, term: str) -> list[dict]:
        url = self.build_search_url(term)
        request = Request(
            url,
            headers={
                "User-Agent": "JobMentor/0.1 (+https://github.com/your-org/job_mentor)",
                "Accept": "application/json, text/html;q=0.9, */*;q=0.8",
            },
        )

        try:
            with urlopen(request, timeout=20) as response:
                payload = response.read().decode("utf-8", errors="ignore")
        except Exception as exc:  # pragma: no cover - network failures are isolated and logged
            logger.warning("Failed to collect jobs from %s for term '%s': %s", self.source_name, term, exc)
            return []

        if not payload:
            return []

        try:
            parsed = json.loads(payload)
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, dict)]
            if isinstance(parsed, dict):
                for key in ("jobs", "results", "items", "data"):
                    items = parsed.get(key)
                    if isinstance(items, list):
                        return [item for item in items if isinstance(item, dict)]
                if "content" in parsed:
                    return []
        except json.JSONDecodeError:
            return []

        return []

    def search_jobs(self, terms: list[str] | None = None, days: int = 14, **kwargs) -> list[Job]:
        active_terms = terms or self.search_terms
        jobs: list[Job] = []

        for term in active_terms:
            if not term or not term.strip():
                continue
            for raw_job in self.fetch_raw_jobs(term):
                normalized = self.normalize_raw_job(raw_job)
                if normalized is None:
                    continue
                if normalized.posted_date is None:
                    continue
                if not is_within_search_window(normalized.posted_date, days=days):
                    continue
                normalized.country = "Germany"
                normalized.source = self.source_name
                jobs.append(normalized)

        return jobs
