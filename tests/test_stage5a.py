from __future__ import annotations

from datetime import date, timedelta

from job_mentor.collectors.arbeitsagentur import ArbeitsagenturCollector
from job_mentor.collectors.meinestadt import MeinestadtCollector
from job_mentor.collectors.stepstone import StepStoneCollector
from job_mentor.config.settings import load_settings
from job_mentor.matching.engine import MatchingEngine
from job_mentor.utils.dates import is_within_search_window


def test_stepstone_adapter_initializes_as_disabled_by_default():
    collector = StepStoneCollector()
    assert collector.source_name == "stepstone.de"
    assert collector.enabled is False
    assert collector.search_jobs() == []


def test_meinestadt_adapter_initializes_as_disabled_by_default():
    collector = MeinestadtCollector()
    assert collector.source_name == "meinestadt.de"
    assert collector.enabled is False
    assert collector.search_jobs() == []


def test_stepstone_adapter_reports_disabled_reason():
    collector = StepStoneCollector()
    status = collector.get_status()
    assert status["portal"] == "stepstone.de"
    assert status["status"] in {"disabled", "not_configured"}
    assert "authorization" in status["reason"].lower() or "configured" in status["reason"].lower()


def test_meinestadt_adapter_reports_disabled_reason():
    collector = MeinestadtCollector()
    status = collector.get_status()
    assert status["portal"] == "meinestadt.de"
    assert status["status"] in {"disabled", "not_configured"}
    assert "public" in status["reason"].lower() or "configured" in status["reason"].lower()


def test_stage5a_configuration_loading_includes_portal_flags():
    settings = load_settings()
    assert hasattr(settings, "arbeitsagentur_enabled")
    assert hasattr(settings, "stepstone_enabled")
    assert hasattr(settings, "meinestadt_enabled")


def test_normalization_preserves_core_job_fields_for_public_payloads():
    collector = MeinestadtCollector(enabled=True)
    raw_job = {
        "title": "Polymer Scientist",
        "company": "Polymer Labs GmbH",
        "location": "Berlin",
        "country": "Germany",
        "source_job_id": "meine-123",
        "url": "https://jobs.meinestadt.de/job/123?utm_source=test",
        "description": "Research polymer formulations and materials performance.",
        "posted_date": "2026-09-25",
    }
    job = collector.normalize_raw_job(raw_job)
    assert job is not None
    assert job.title == "Polymer Scientist"
    assert job.company == "Polymer Labs GmbH"
    assert job.location == "Berlin"
    assert job.country == "Germany"
    assert job.url == "https://jobs.meinestadt.de/job/123"
    assert job.source_job_id == "meine-123"
    assert job.description is not None
    assert job.posted_date is not None


def test_date_filtering_rejects_old_and_future_jobs():
    today = date.today()
    old_date = (today - timedelta(days=20)).isoformat()
    recent_date = (today - timedelta(days=5)).isoformat()
    future_date = (today + timedelta(days=1)).isoformat()

    assert is_within_search_window(old_date, days=14) is False
    assert is_within_search_window(recent_date, days=14) is True
    assert is_within_search_window(future_date, days=14) is False
    assert is_within_search_window("", days=14) is False


def test_matching_engine_accepts_collector_output_for_relevant_jobs():
    collector = MeinestadtCollector(enabled=True)
    job = collector.normalize_raw_job({
        "title": "Rubber Technology Engineer",
        "company": "ElastoTech GmbH",
        "location": "Düsseldorf",
        "description": "Lead rubber formulation and compounding programs for automotive seals.",
        "source_job_id": "rub-77",
        "url": "https://jobs.meinestadt.de/job/rub-77",
        "posted_date": "2026-09-28",
    })
    result = MatchingEngine().score_job(job)
    assert result.score >= 40
    assert result.category in {"GOOD_MATCH", "STRONG_MATCH"}
    assert len(result.reasons) > 0
    assert job.match_score >= 40


def test_disabled_portals_do_not_stop_multi_portal_collection():
    collectors = [
        ArbeitsagenturCollector(),
        StepStoneCollector(),
        MeinestadtCollector(),
    ]
    results = []
    for collector in collectors:
        try:
            results.append(collector.search_jobs())
        except Exception as exc:  # pragma: no cover - defensive assertion for isolation
            raise AssertionError(f"Portal failure leaked across adapters: {exc}") from exc

    assert len(results) == 3
    assert all(isinstance(r, list) for r in results)


def test_stepstone_disabled_adapter_does_not_require_credentials_for_safe_failure():
    collector = StepStoneCollector(enabled=False)
    assert collector.search_jobs() == []
    assert collector.enabled is False


def test_meinestadt_disabled_adapter_does_not_require_credentials_for_safe_failure():
    collector = MeinestadtCollector(enabled=False)
    assert collector.search_jobs() == []
    assert collector.enabled is False


def test_env_toggle_can_disable_stepstone_without_crashing(monkeypatch):
    monkeypatch.setenv("STEPSTONE_ENABLED", "false")
    collector = StepStoneCollector()
    assert collector.enabled is False
    assert collector.search_jobs() == []


def test_env_toggle_can_disable_meinestadt_without_crashing(monkeypatch):
    monkeypatch.setenv("MEINESTADT_ENABLED", "false")
    collector = MeinestadtCollector()
    assert collector.enabled is False
    assert collector.search_jobs() == []
