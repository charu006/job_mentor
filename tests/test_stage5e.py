from __future__ import annotations

from job_mentor.collectors.irishjobs import IrishJobsCollector
from job_mentor.collectors.publicjobs import PublicJobsCollector
from job_mentor.collectors.recruitireland import RecruitIrelandCollector
from job_mentor.config.settings import load_settings


def test_publicjobs_adapter_is_disabled_by_default():
    collector = PublicJobsCollector()
    assert collector.source_name == "publicjobs.ie"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_irishjobs_adapter_is_disabled_by_default():
    collector = IrishJobsCollector()
    assert collector.source_name == "irishjobs.ie"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_recruitireland_adapter_is_disabled_by_default():
    collector = RecruitIrelandCollector()
    assert collector.source_name == "recruitireland.com"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_stage5e_settings_expose_irish_flags():
    settings = load_settings()
    assert hasattr(settings, "publicjobs_enabled")
    assert hasattr(settings, "irishjobs_enabled")
    assert hasattr(settings, "recruitireland_enabled")
    assert settings.publicjobs_enabled is False
    assert settings.irishjobs_enabled is False
    assert settings.recruitireland_enabled is False


def test_irish_collectors_fail_gracefully_when_disabled():
    collectors = [
        PublicJobsCollector(),
        IrishJobsCollector(),
        RecruitIrelandCollector(),
    ]
    results = [collector.search_jobs() for collector in collectors]
    assert all(result == [] for result in results)


def test_irish_collectors_normalize_common_job_fields():
    raw_job = {
        "title": "Polymer Engineer",
        "company": "Irish Materials Ltd",
        "location": "Dublin",
        "description": "Design and develop polymer and elastomer products for industrial use.",
        "url": "https://example.com/jobs/abc?ref=source",
        "id": "IE-100",
        "published_at": "2026-09-25T12:00:00Z",
    }
    for collector in [PublicJobsCollector(), IrishJobsCollector(), RecruitIrelandCollector()]:
        normalized = collector.normalize_raw_job(raw_job)
        assert normalized is not None
        assert normalized.title == "Polymer Engineer"
        assert normalized.company == "Irish Materials Ltd"
        assert normalized.source == collector.source_name
        assert normalized.url == "https://example.com/jobs/abc"
        assert normalized.country == "Ireland"
