from __future__ import annotations

import logging
import os
from typing import Any
from xml.etree import ElementTree as ET
from urllib.error import URLError
from urllib.request import Request

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job
from job_mentor.network import urlopen_with_reliable_ssl as urlopen

logger = logging.getLogger("job_mentor.collectors.net_empregos")


class NetEmpregosCollector(BaseCollector):
    """Official RSS-feed collector for net-empregos.com.

    The project uses the public RSS feed published by the site itself rather than
    scraping the HTML interface. This remains disabled by default and only runs
    when explicitly enabled, preserving the project’s safety-first rules.
    """

    source_name = "net-empregos.com"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.net-empregos.com",
        feed_url: str | None = None,
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.feed_url = (feed_url or os.getenv("NET_EMPREGOS_FEED_URL", "https://www.net-empregos.com/rssfeed.asp")).rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("NET_EMPREGOS_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def _fetch_feed(self) -> str:
        request = Request(self.feed_url, headers={"User-Agent": "JobMentor/0.1"})
        try:
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="ignore")
        except (URLError, TimeoutError, OSError) as exc:
            logger.warning("Could not fetch Net Empregos RSS feed: %s", exc)
            return ""

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Net Empregos remains disabled by default; only the official RSS feed is used when explicitly enabled.",
            }
        return {
            "portal": self.source_name,
            "status": "active",
            "reason": "Official RSS feed access is configured and enabled for this project.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Net Empregos adapter is disabled; no explicit feed-enabled configuration is active.")
            return []

        feed_xml = self._fetch_feed()
        if not feed_xml:
            logger.warning("Net Empregos feed returned no XML payload; skipping collection.")
            return []

        try:
            root = ET.fromstring(feed_xml)
        except ET.ParseError as exc:
            logger.warning("Net Empregos RSS feed could not be parsed: %s", exc)
            return []

        jobs: list[Job] = []
        for item in root.findall(".//item"):
            title = item.findtext("title") or item.findtext("title/")
            link = item.findtext("link")
            description = item.findtext("description")
            source_job_id = item.findtext("guid") or item.findtext("id") or link
            posted_date = item.findtext("pubDate") or item.findtext("published")
            if not title:
                continue
            normalized = self.normalize_raw_job({
                "title": title,
                "url": link,
                "description": description,
                "source_job_id": source_job_id,
                "posted_date": posted_date,
            })
            if normalized is not None:
                normalized.country = "Portugal"
                normalized.source = self.source_name
                jobs.append(normalized)
        return jobs

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Portugal"
        job.source = self.source_name
        return job
