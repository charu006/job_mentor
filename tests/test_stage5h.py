from __future__ import annotations

from job_mentor.collectors.academic_work import AcademicWorkCollector
from job_mentor.collectors.arbetsformedlingen import ArbetsformedlingenCollector
from job_mentor.collectors.jobbsafari import JobbSafariCollector
from job_mentor.config.settings import load_settings


def test_sweden_settings_expose_flags():
    settings = load_settings()
    assert hasattr(settings, "arbetsformedlingen_enabled")
    assert hasattr(settings, "academicwork_enabled")
    assert hasattr(settings, "jobbsafari_enabled")
    assert settings.arbetsformedlingen_enabled is True
    assert settings.academicwork_enabled is False
    assert settings.jobbsafari_enabled is False


def test_academic_work_defaults_disabled():
    collector = AcademicWorkCollector()
    assert collector.source_name == "academicwork.se"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_jobbsafari_defaults_disabled():
    collector = JobbSafariCollector()
    assert collector.source_name == "jobbsafari.se"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_disabled_collectors_do_not_make_network_calls():
    collectors = [
        AcademicWorkCollector(),
        JobbSafariCollector(),
    ]
    for collector in collectors:
        assert collector.search_jobs() == []


def test_arbetsformedlingen_uses_official_api_path():
    collector = ArbetsformedlingenCollector(enabled=True)
    assert collector.api_base_url == "https://jobsearch.api.jobtechdev.se"
    assert collector.search_url.endswith("/search")
    assert "platsbanken" not in collector.search_url.lower()
    assert "html" not in collector.search_url.lower()


def test_arbetsformedlingen_parses_public_api_response(monkeypatch):
    collector = ArbetsformedlingenCollector(enabled=True)

    sample = {
        "total": {"value": 1},
        "hits": [{
            "id": "SE-1001",
            "title": "Polymer Engineer",
            "employer": {"name": "Nordic Polymer Labs"},
            "location": {"municipality": "Stockholm", "region": "Stockholm"},
            "description": {"text": "Develop polymer and elastomer products."},
            "url": "https://example.se/jobs/se-1001",
            "published": "2026-09-14T12:00:00Z",
        }],
    }

    monkeypatch.setattr(collector, "_fetch_search_page", lambda q="polymer", offset=0, limit=10: sample)
    jobs = collector.search_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Polymer Engineer"
    assert jobs[0].company == "Nordic Polymer Labs"
    assert jobs[0].location == "Stockholm"
    assert jobs[0].country == "Sweden"
    assert jobs[0].source == "arbetsformedlingen.se"
    assert jobs[0].source_job_id == "SE-1001"
    assert jobs[0].url == "https://example.se/jobs/se-1001"


def test_arbetsformedlingen_prefers_live_publication_fields(monkeypatch):
    collector = ArbetsformedlingenCollector(enabled=True)

    sample = {
        "total": {"value": 1},
        "hits": [{
            "id": "SE-2002",
            "title": "R&D Engineer in Polymer Materials",
            "employer": {"name": "NKT"},
            "location": {"municipality": "Karlskrona"},
            "description": {"text": "Polymer materials and technology."},
            "webpage_url": "https://example.se/jobs/se-2002",
            "publication_date": "2026-09-16T15:25:02",
            "last_publication_date": "2026-09-30T23:59:59",
            "application_deadline": "2026-09-30T23:59:59",
        }],
    }

    monkeypatch.setattr(collector, "_fetch_search_page", lambda q="polymer", offset=0, limit=10: sample)
    jobs = collector.search_jobs()
    assert len(jobs) == 1
    assert jobs[0].posted_date is not None
    assert str(jobs[0].posted_date).startswith("2026-09-16") or str(jobs[0].posted_date).startswith("2026-09-30")


def test_arbetsformedlingen_enforces_global_request_cap(monkeypatch):
    collector = ArbetsformedlingenCollector(enabled=True, max_requests=3)
    calls = []

    def fake_fetch(q=None, offset=0, limit=10):
        calls.append((q, offset, limit))
        return {
            "total": {"value": 10},
            "hits": [{
                "id": f"{q}-{offset}",
                "title": f"Role for {q}",
                "url": f"https://example.se/{q}/{offset}",
            }],
        }

    monkeypatch.setattr(collector, "_fetch_search_page", fake_fetch)
    jobs = collector.search_jobs(terms=["polymer", "elastomer", "rubber technology"], limit=1, max_pages=10)
    assert len(calls) == 3
    assert len(jobs) == 3
    assert all(call[2] == 1 for call in calls)
    assert calls[0][0] == "polymer"
    assert len({call[0] for call in calls}) == 1


def test_arbetsformedlingen_handles_pagination_and_errors(monkeypatch):
    collector = ArbetsformedlingenCollector(enabled=True)

    calls = []

    def fake_fetch(q=None, offset=0, limit=10):
        calls.append((offset, limit))
        if offset == 0:
            return {"total": {"value": 2}, "hits": [{"id": "A", "title": "Rubber Engineer", "url": "https://example.se/a"}, {"id": "B", "title": "Material Developer", "url": "https://example.se/b"}]}
        if offset == 2:
            return {"total": {"value": 2}, "hits": []}
        return {"total": {"value": 2}, "hits": []}

    monkeypatch.setattr(collector, "_fetch_search_page", fake_fetch)
    jobs = collector.search_jobs(limit=2)
    assert len(jobs) == 2
    assert calls[0][0] == 0
    assert calls[0][1] == 2

    def fail_fetch(q=None, offset=0, limit=10):
        raise RuntimeError("temporary API error")

    collector_fail = ArbetsformedlingenCollector(enabled=True)
    monkeypatch.setattr(collector_fail, "_fetch_search_page", fail_fetch)
    assert collector_fail.search_jobs() == []
