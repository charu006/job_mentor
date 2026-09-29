from __future__ import annotations

from job_mentor.collectors.jobnet import JobNetCollector
from job_mentor.collectors.ofir import OfirCollector
from job_mentor.collectors.workindenmark import WorkindenmarkCollector
from job_mentor.config.settings import load_settings


def test_jobnet_adapter_is_disabled_by_default():
    collector = JobNetCollector()
    assert collector.source_name == "jobnet.dk"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_ofir_adapter_is_disabled_by_default():
    collector = OfirCollector()
    assert collector.source_name == "ofir.dk"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_workindenmark_adapter_is_disabled_by_default():
    collector = WorkindenmarkCollector()
    assert collector.source_name == "workindenmark.dk"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_stage5d_settings_expose_danish_flags():
    settings = load_settings()
    assert hasattr(settings, "jobnet_enabled")
    assert hasattr(settings, "ofir_enabled")
    assert hasattr(settings, "workindenmark_enabled")
    assert settings.jobnet_enabled is False
    assert settings.ofir_enabled is False
    assert settings.workindenmark_enabled is False


def test_danish_collectors_fail_gracefully_when_disabled():
    collectors = [
        JobNetCollector(),
        OfirCollector(),
        WorkindenmarkCollector(),
    ]
    results = [collector.search_jobs() for collector in collectors]
    assert all(result == [] for result in results)


def test_danish_collectors_normalize_common_job_fields():
    raw_job = {
        "title": "Polymer Scientist",
        "company": "Nordic Materials A/S",
        "location": "Copenhagen",
        "description": "Develop polymer and elastomer products for industrial applications.",
        "url": "https://example.com/jobs/123?ref=source",
        "id": "DK-123",
        "published_at": "2026-09-25T12:00:00Z",
    }
    for collector in [JobNetCollector(), OfirCollector(), WorkindenmarkCollector()]:
        normalized = collector.normalize_raw_job(raw_job)
        assert normalized is not None
        assert normalized.title == "Polymer Scientist"
        assert normalized.company == "Nordic Materials A/S"
        assert normalized.source == collector.source_name
        assert normalized.url == "https://example.com/jobs/123"
        assert normalized.country == "Denmark"
