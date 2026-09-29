from __future__ import annotations

import json
from datetime import date, timedelta
from urllib.error import HTTPError

from job_mentor.collectors.jobdigger import JobDiggerCollector
from job_mentor.collectors.nationalevacaturebank import NationaleVacaturebankCollector
from job_mentor.collectors.werk_nl import WerkNLCollector
from job_mentor.config.settings import load_settings
from job_mentor.matching.engine import MatchingEngine
from job_mentor.utils.dates import is_within_search_window


class DummyResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({
            "jobs": [{
                "title": "Polymer Scientist",
                "company": "PolymerLab BV",
                "location": "Rotterdam",
                "reference": "job-123",
                "url": "https://www.jobdigger.com/jobs/job-123",
                "description": "Research polymer formulations and elastomer systems.",
                "date": (date.today() - timedelta(days=2)).isoformat(),
            }]
        }).encode("utf-8")


def test_work_nl_adapter_is_disabled_by_default():
    collector = WerkNLCollector()
    assert collector.source_name == "werk.nl"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_nationalevacaturebank_adapter_is_disabled_by_default():
    collector = NationaleVacaturebankCollector()
    assert collector.source_name == "nationalevacaturebank.nl"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_jobdigger_requires_api_key_when_enabled():
    collector = JobDiggerCollector(enabled=True)
    assert collector.enabled is True
    assert collector.is_configured is False
    assert collector.get_status()["status"] == "api-key-required"
    assert collector.search_jobs() == []


def test_jobdigger_parses_mocked_search_payload():
    collector = JobDiggerCollector(enabled=True, api_key="demo-key")

    def fake_urlopen(_request, timeout=20):
        return DummyResponse()

    import job_mentor.collectors.jobdigger as module

    original = module.urlopen
    module.urlopen = fake_urlopen
    try:
        jobs = collector.search_jobs(terms=["polymer"], days=14)
    finally:
        module.urlopen = original

    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Polymer Scientist"
    assert job.company == "PolymerLab BV"
    assert job.location == "Rotterdam"
    assert job.country == "Netherlands"
    assert job.source == "jobdigger.nl"
    assert job.source_job_id == "job-123"
    assert job.url == "https://www.jobdigger.com/jobs/job-123"
    assert is_within_search_window(job.posted_date, days=14) is True


def test_jobdigger_gracefully_handles_network_errors():
    collector = JobDiggerCollector(enabled=True, api_key="demo-key")

    def fake_error(_request, timeout=20):
        raise HTTPError("https://api.jobdigger.com/v2/search", 401, "Unauthorized", hdrs=None, fp=None)

    import job_mentor.collectors.jobdigger as module

    original = module.urlopen
    module.urlopen = fake_error
    try:
        jobs = collector.search_jobs(terms=["elastomer"], days=14)
    finally:
        module.urlopen = original

    assert jobs == []


def test_jobdigger_matches_existing_engine_output():
    collector = JobDiggerCollector(enabled=True, api_key="demo-key")
    raw = {
        "title": "Rubber Technology Engineer",
        "company": "ElastoWorks BV",
        "location": "Arnhem",
        "reference": "rub-88",
        "url": "https://jobs.example/rub-88",
        "description": "Lead rubber formulation and compounding programs for sealing applications.",
        "date": (date.today() - timedelta(days=3)).isoformat(),
    }
    job = collector.normalize_raw_job(raw)
    assert job is not None
    result = MatchingEngine().score_job(job)
    assert result.score >= 40
    assert result.category in {"GOOD_MATCH", "STRONG_MATCH"}
    assert len(result.reasons) > 0


def test_stage5b_settings_expose_all_netherlands_flags():
    settings = load_settings()
    assert hasattr(settings, "werk_nl_enabled")
    assert hasattr(settings, "nationalevacaturebank_enabled")
    assert hasattr(settings, "jobdigger_enabled")
    assert hasattr(settings, "jobdigger_api_key")
    assert settings.werk_nl_enabled is False
    assert settings.nationalevacaturebank_enabled is False


def test_disabled_netherlands_portals_do_not_stop_pipeline():
    collectors = [
        WerkNLCollector(),
        NationaleVacaturebankCollector(),
        JobDiggerCollector(),
    ]
    results = []
    for collector in collectors:
        results.append(collector.search_jobs())
    assert all(result == [] for result in results)
