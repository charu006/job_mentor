from __future__ import annotations

from datetime import date, timedelta

from job_mentor.collectors.arbeit_swiss import ArbeitSwissCollector
from job_mentor.collectors.jobup_ch import JobUpCHCollector
from job_mentor.collectors.jobs_ch import JobsCHCollector
from job_mentor.config.settings import load_settings
from job_mentor.matching.engine import MatchingEngine
from job_mentor.utils.dates import is_within_search_window


def test_arbeit_swiss_adapter_is_disabled_by_default():
    collector = ArbeitSwissCollector()
    assert collector.source_name == "arbeit.swiss"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_jobs_ch_adapter_is_disabled_by_default():
    collector = JobsCHCollector()
    assert collector.source_name == "jobs.ch"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_jobup_ch_adapter_is_disabled_by_default():
    collector = JobUpCHCollector()
    assert collector.source_name == "jobup.ch"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_stage5c_settings_expose_swiss_flags():
    settings = load_settings()
    assert hasattr(settings, "arbeit_swiss_enabled")
    assert hasattr(settings, "jobs_ch_enabled")
    assert hasattr(settings, "jobup_ch_enabled")
    assert settings.arbeit_swiss_enabled is False
    assert settings.jobs_ch_enabled is False
    assert settings.jobup_ch_enabled is False


def test_swiss_collectors_do_not_crash_pipeline_when_disabled():
    collectors = [
        ArbeitSwissCollector(),
        JobsCHCollector(),
        JobUpCHCollector(),
    ]
    results = [collector.search_jobs() for collector in collectors]
    assert all(result == [] for result in results)


def test_swiss_disabled_collectors_return_safe_status():
    status = [
        ArbeitSwissCollector().get_status(),
        JobsCHCollector().get_status(),
        JobUpCHCollector().get_status(),
    ]
    assert all(item["status"] == "disabled" for item in status)


def test_dynamic_date_window_stays_valid_for_swiss_pipeline():
    today = date.today()
    old_date = (today - timedelta(days=25)).isoformat()
    recent_date = (today - timedelta(days=3)).isoformat()
    future_date = (today + timedelta(days=2)).isoformat()

    assert is_within_search_window(old_date, days=14) is False
    assert is_within_search_window(recent_date, days=14) is True
    assert is_within_search_window(future_date, days=14) is False


def test_matching_engine_remains_unchanged_with_swiss_safe_adapter_data():
    job = {
        "title": "Polymer Scientist",
        "company": "Swiss Materials AG",
        "location": "Zurich",
        "description": "Lead polymer and elastomer development work for technical materials projects.",
        "source_job_id": "ch-001",
        "url": "https://example.com/ch-001",
        "posted_date": (date.today() - timedelta(days=2)).isoformat(),
    }
    collector = ArbeitSwissCollector()
    normalized = collector.normalize_raw_job(job)
    assert normalized is not None
    result = MatchingEngine().score_job(normalized)
    assert result.score >= 40
    assert result.category in {"GOOD_MATCH", "STRONG_MATCH"}
