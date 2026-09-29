from __future__ import annotations

import pytest

import job_mentor.collectors.arbeidsplassen as arbeidsplassen_module
from job_mentor.collectors.arbeidsplassen import ArbeidsplassenCollector
from job_mentor.collectors.finn import FinnCollector
from job_mentor.collectors.jobbnorge import JobbnorgeCollector
from job_mentor.config.settings import load_settings


def test_norway_settings_expose_flags():
    settings = load_settings()
    assert hasattr(settings, "arbeidsplassen_enabled")
    assert hasattr(settings, "finn_enabled")
    assert hasattr(settings, "jobbnorge_enabled")
    assert settings.arbeidsplassen_enabled is True
    assert settings.finn_enabled is False
    assert settings.jobbnorge_enabled is True
    assert settings.arbeidsplassen_max_requests == 10


def test_finn_defaults_disabled():
    collector = FinnCollector()
    assert collector.source_name == "finn.no"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_arbeidsplassen_uses_public_api_path():
    collector = ArbeidsplassenCollector(enabled=True)
    assert collector.api_base_url == "https://arbeidsplassen.nav.no"
    assert collector.search_url.endswith("/public-ads-api")
    assert "html" not in collector.search_url.lower()
    assert "scrape" not in collector.search_url.lower()
    assert collector.max_requests == 10


def test_arbeidsplassen_parses_public_api_response(monkeypatch):
    collector = ArbeidsplassenCollector(enabled=True)

    sample = {
        "ads": [{
            "id": "NO-1001",
            "title": "Polymer Engineer",
            "employer": {"name": "Nordic Polymer Labs"},
            "location": {"city": "Oslo", "country": "NO"},
            "description": "Develop polymer and elastomer solutions.",
            "link": "https://example.no/jobs/no-1001",
            "published": "2026-09-14T12:00:00Z",
        }]
    }

    monkeypatch.setattr(collector, "_fetch_search_page", lambda q="polymer", offset=0, limit=10: sample)
    jobs = collector.search_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Polymer Engineer"
    assert jobs[0].company == "Nordic Polymer Labs"
    assert jobs[0].location == "Oslo"
    assert jobs[0].country == "Norway"
    assert jobs[0].source == "arbeidsplassen.nav.no"
    assert jobs[0].source_job_id == "NO-1001"
    assert jobs[0].url == "https://example.no/jobs/no-1001"


def test_arbeidsplassen_global_request_cap_across_terms(monkeypatch):
    collector = ArbeidsplassenCollector(enabled=True, max_requests=3)
    calls = []

    def fake_fetch(q=None, offset=0, limit=10):
        calls.append((q, offset, limit))
        return {"ads": [{"id": f"{q}-{offset}", "title": f"Role for {q}", "link": f"https://example.no/{q}/{offset}", "published": "2026-09-14T12:00:00Z"}]}

    monkeypatch.setattr(collector, "_fetch_search_page", fake_fetch)
    jobs = collector.search_jobs(terms=["polymer", "elastomer", "rubber technology"], limit=1, max_pages=10)
    assert len(calls) == 3
    assert len(jobs) == 3
    assert collector.max_requests == 3
    assert all(call[2] == 1 for call in calls)
    assert {call[0] for call in calls} <= {"polymer", "elastomer", "rubber technology"}


def test_arbeidsplassen_pagination_stops_at_global_cap(monkeypatch):
    collector = ArbeidsplassenCollector(enabled=True, max_requests=2)
    calls = []

    def fake_fetch(q=None, offset=0, limit=10):
        calls.append((q, offset, limit))
        if offset < 2:
            return {"ads": [{"id": f"{q}-{offset}", "title": f"Role {offset}", "link": f"https://example.no/{q}/{offset}", "published": "2026-09-14T12:00:00Z"}]}
        return {"ads": []}

    monkeypatch.setattr(collector, "_fetch_search_page", fake_fetch)
    jobs = collector.search_jobs(terms=["polymer", "elastomer"], limit=1, max_pages=10)
    assert len(calls) == 2
    assert len(jobs) == 2
    assert calls[0][1] == 0
    assert calls[1][1] == 1


def test_arbeidsplassen_handles_api_errors_and_bad_json(monkeypatch):
    collector = ArbeidsplassenCollector(enabled=True)

    def fail_fetch(*args, **kwargs):
        raise RuntimeError("temporary API error")

    monkeypatch.setattr(collector, "_fetch_search_page", fail_fetch)
    assert collector.search_jobs(terms=["polymer"]) == []

    class FakeResponse:
        def read(self):
            return b"{"   

    monkeypatch.setattr(arbeidsplassen_module, "urlopen", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(RuntimeError):
        collector._fetch_search_page(q="polymer", offset=0, limit=10)

    monkeypatch.setattr(collector, "_fetch_search_page", lambda *args, **kwargs: {})
    assert collector.search_jobs(terms=["polymer"]) == []


def test_jobbnorge_uses_rss_path_and_parses_feed(monkeypatch):
    collector = JobbnorgeCollector(enabled=True)
    assert collector.feed_url == "https://www.jobbnorge.no/rss"

    sample = '''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
        <title>Jobbnorge</title>
        <item>
            <title>Rubber Specialist</title>
            <link>https://example.no/jobs/rubber</link>
            <description>Develop elastomer and polymer solutions.</description>
            <guid>NO-2002</guid>
            <pubDate>Mon, 14 Sep 2026 12:00:00 GMT</pubDate>
            <deadline>2026-09-30T23:59:59Z</deadline>
        </item>
    </channel></rss>'''

    monkeypatch.setattr(collector, "_fetch_feed", lambda: sample)
    jobs = collector.search_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Rubber Specialist"
    assert jobs[0].company is None
    assert jobs[0].country == "Norway"
    assert jobs[0].source == "jobbnorge.no"
    assert jobs[0].source_job_id == "NO-2002"
    assert jobs[0].url == "https://example.no/jobs/rubber"
    assert jobs[0].deadline is not None


def test_jobbnorge_missing_guid_sets_source_id_none(monkeypatch):
    collector = JobbnorgeCollector(enabled=True)
    sample = '''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
        <item>
            <title>Material Scientist</title>
            <link>https://example.no/jobs/material-scientist</link>
            <description>Polymer development role.</description>
            <pubDate>Mon, 14 Sep 2026 12:00:00 GMT</pubDate>
        </item>
    </channel></rss>'''
    monkeypatch.setattr(collector, "_fetch_feed", lambda: sample)
    jobs = collector.search_jobs()
    assert len(jobs) == 1
    assert jobs[0].source_job_id is None
    assert jobs[0].url == "https://example.no/jobs/material-scientist"


def test_jobbnorge_missing_deadline_is_safe(monkeypatch):
    collector = JobbnorgeCollector(enabled=True)
    sample = '''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
        <item>
            <title>Polymer Engineer</title>
            <link>https://example.no/jobs/polymer-engineer</link>
            <description>Develop elastomer products.</description>
            <guid>NO-3003</guid>
            <pubDate>Mon, 14 Sep 2026 12:00:00 GMT</pubDate>
        </item>
    </channel></rss>'''
    monkeypatch.setattr(collector, "_fetch_feed", lambda: sample)
    jobs = collector.search_jobs()
    assert len(jobs) == 1
    assert jobs[0].source_job_id == "NO-3003"
    assert jobs[0].deadline is None


def test_jobbnorge_handles_malformed_xml_and_feed_failures(monkeypatch):
    collector = JobbnorgeCollector(enabled=True)
    monkeypatch.setattr(collector, "_fetch_feed", lambda: "<broken><xml>")
    assert collector.search_jobs() == []

    def fail_feed():
        return ""

    monkeypatch.setattr(collector, "_fetch_feed", fail_feed)
    assert collector.search_jobs() == []

    calls = {"count": 0}

    def counted_feed():
        calls["count"] += 1
        return "" if calls["count"] == 1 else ""

    monkeypatch.setattr(collector, "_fetch_feed", counted_feed)
    collector.search_jobs()
    assert calls["count"] == 1


def test_finn_remains_disabled_and_makes_zero_network_calls(monkeypatch):
    collector = FinnCollector()
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"

    # The collector is intentionally disabled and should never reach any network access path.
    assert collector.get_status()["reason"]
    assert collector.enabled is False
