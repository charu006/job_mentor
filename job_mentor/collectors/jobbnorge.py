from __future__ import annotations

import logging
import os
import re
from typing import Any
from urllib.error import URLError
from urllib.request import Request
from xml.etree import ElementTree as ET

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.models.job import Job
from job_mentor.network import urlopen_with_reliable_ssl as urlopen

logger = logging.getLogger("job_mentor.collectors.jobbnorge")


class JobbnorgeCollector(BaseCollector):
    """Official RSS-feed collector for Jobbnorge.

    The project uses the public RSS feed published by the site itself rather than
    scraping the HTML interface. This remains enabled by default because the RSS
    feed is a documented public channel intended for clients and indexing.
    """

    source_name = "jobbnorge.no"

    def __init__(
        self,
        search_terms: list[str] | None = None,
        enabled: bool | None = None,
        base_url: str = "https://www.jobbnorge.no",
        feed_url: str | None = None,
    ):
        super().__init__(search_terms or list(DEFAULT_SEARCH_TERMS))
        self.base_url = base_url.rstrip("/")
        self.feed_url = (feed_url or os.getenv("JOBBNORGE_FEED_URL", "https://www.jobbnorge.no/rss")).rstrip("/")
        self.enabled = self._resolve_enabled(enabled)

    def _resolve_enabled(self, override: bool | None) -> bool:
        if override is not None:
            return bool(override)
        raw_value = os.getenv("JOBBNORGE_ENABLED", "false").strip().lower()
        return raw_value in {"1", "true", "yes", "on"}

    def _fetch_feed(self) -> str:
        request = Request(self.feed_url, headers={"User-Agent": "JobMentor/0.1"})
        try:
            with urlopen(request, timeout=20) as response:
                return response.read().decode("utf-8", errors="ignore")
        except (URLError, TimeoutError, OSError) as exc:
            logger.warning("Could not fetch Jobbnorge RSS feed: %s", exc)
            return ""

    @staticmethod
    def _sanitize_feed_xml(feed_xml: str) -> str:
        if not feed_xml:
            return ""
        xml = feed_xml.strip()
        if not xml:
            return ""
        xml = re.sub(r"&(?!(?:#\d+;|#x[0-9A-Fa-f]+;|amp;|lt;|gt;|quot;|apos;))([A-Za-z][A-Za-z0-9]+;)", r"&amp;\1", xml)
        return xml

    def get_status(self) -> dict[str, str]:
        if not self.enabled:
            return {
                "portal": self.source_name,
                "status": "disabled",
                "reason": "Jobbnorge remains disabled by configuration until explicitly enabled.",
            }
        return {
            "portal": self.source_name,
            "status": "active",
            "reason": "Official Jobbnorge RSS feed access is configured and enabled for this project.",
        }

    def search_jobs(self, terms: list[str] | None = None, **kwargs) -> list[Job]:
        if not self.enabled:
            logger.info("Jobbnorge adapter is disabled; no explicit feed-enabled configuration is active.")
            return []

        feed_xml = self._fetch_feed()
        if not feed_xml:
            logger.warning("Jobbnorge feed returned no XML payload; skipping collection.")
            return []

        sanitized_feed = self._sanitize_feed_xml(feed_xml)
        try:
            root = ET.fromstring(sanitized_feed)
        except ET.ParseError as exc:
            logger.warning("Jobbnorge RSS feed could not be parsed: %s", exc)
            return []

        jobs: list[Job] = []
        for item in root.findall(".//item"):
            title = item.findtext("title")
            link = item.findtext("link")
            description = item.findtext("description")
            source_job_id = item.findtext("guid") or item.findtext("id") or None
            posted_date = item.findtext("pubDate") or item.findtext("published")
            deadline = (
                item.findtext("deadline")
                or item.findtext("applicationDeadline")
                or item.findtext("application-deadline")
                or item.findtext("validThrough")
                or item.findtext("closingDate")
                or item.findtext("expires")
                or None
            )
            if not title:
                continue
            normalized = self.normalize_raw_job({
                "title": title,
                "url": link,
                "description": description,
                "source_job_id": source_job_id,
                "posted_date": posted_date,
                "deadline": deadline,
            })
            if normalized is not None:
                normalized.country = "Norway"
                normalized.source = self.source_name
                jobs.append(normalized)
        return jobs

    def normalize_raw_job(self, raw_job: dict[str, Any]) -> Job | None:
        job = super().normalize_raw_job(raw_job)
        if job is None:
            return None
        if job.url and "?" in job.url:
            job.url = job.url.split("?", 1)[0]
        job.country = "Norway"
        job.source = self.source_name
        if raw_job.get("source_job_id"):
            job.source_job_id = str(raw_job["source_job_id"])
        else:
            job.source_job_id = None
        if raw_job.get("deadline"):
            job.deadline = str(raw_job["deadline"])
        else:
            job.deadline = None
        return job
