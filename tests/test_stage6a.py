from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.settings import load_settings
from job_mentor.models.job import Job
from job_mentor.runner import CollectionRunSummary, discover_collectors, run_collection


class FakeCollector(BaseCollector):
    source_name = "fake"

    def __init__(self, jobs=None, enabled=True, base_url=None):
        super().__init__()
        self.enabled = enabled
        self.jobs = jobs or []
        self.base_url = base_url

    def search_jobs(self, terms=None, **kwargs):
        return [Job(**job) for job in self.jobs]


class FailingCollector(BaseCollector):
    source_name = "failing"

    def __init__(self, enabled=True):
        super().__init__()
        self.enabled = enabled

    def search_jobs(self, terms=None, **kwargs):
        raise RuntimeError("boom")


def _make_job(title, company="Acme", location="Berlin", source="fake", source_job_id="id-1", posted_days=0):
    posted = (datetime.now(timezone.utc) - timedelta(days=posted_days)).isoformat()
    return {
        "title": title,
        "company": company,
        "location": location,
        "country": "Germany",
        "source": source,
        "source_job_id": source_job_id,
        "url": f"https://example.com/{source_job_id}",
        "description": "polymer elastomer materials science role",
        "posted_date": posted,
    }


def test_stage6a_runner_discovers_enabled_collectors():
    collectors = discover_collectors()
    assert collectors
    assert all(hasattr(collector, "enabled") for collector in collectors)


def test_stage6a_disabled_collectors_are_skipped(tmp_path, monkeypatch):
    def fake_registry():
        return [FakeCollector(enabled=False, jobs=[]), FakeCollector(enabled=True, jobs=[_make_job("polymer engineer")])]

    monkeypatch.setattr("job_mentor.runner.discover_collectors", fake_registry)
    result = run_collection(db_path=tmp_path / "job.db", collectors=fake_registry())
    assert result.collectors_attempted == 1
    assert result.collectors_skipped == 1
    assert result.failed_collectors == []


def test_stage6a_disabled_collectors_make_zero_network_calls(tmp_path, monkeypatch):
    calls = []

    class ZeroRequestCollector(FakeCollector):
        def search_jobs(self, terms=None, **kwargs):
            calls.append("called")
            return []

    monkeypatch.setattr("job_mentor.runner.discover_collectors", lambda: [ZeroRequestCollector(enabled=False)])
    run_collection(db_path=tmp_path / "job.db", collectors=[ZeroRequestCollector(enabled=False)])
    assert calls == []


def test_stage6a_run_collection_persists_matching_jobs(tmp_path):
    collector_a = FakeCollector(enabled=True, jobs=[_make_job("polymer engineer", source_job_id="a-1", posted_days=1)])
    collector_b = FakeCollector(enabled=True, jobs=[_make_job("rubber technology specialist", source_job_id="b-1", posted_days=2)])
    result = run_collection(db_path=tmp_path / "job.db", collectors=[collector_a, collector_b])
    assert result.raw_jobs_collected >= 2
    assert result.relevant_jobs >= 2
    assert result.new_jobs >= 2
    assert result.duplicates == 0


def test_stage6a_duplicate_jobs_are_not_inserted_twice(tmp_path):
    jobs = [_make_job("polymer scientist", source="collector-a", source_job_id="dup-1", posted_days=1)]
    collector_a = FakeCollector(enabled=True, jobs=jobs)
    collector_b = FakeCollector(enabled=True, jobs=[_make_job("polymer scientist", source="collector-b", source_job_id="dup-1", posted_days=1)])

    result = run_collection(db_path=tmp_path / "job.db", collectors=[collector_a, collector_b])
    assert result.duplicates >= 1
    assert result.new_jobs == 1


def test_stage6a_one_failed_collector_does_not_crash_run(tmp_path):
    collector_a = FakeCollector(enabled=True, jobs=[_make_job("polymer engineer", source_job_id="ok-1", posted_days=1)])
    collector_b = FailingCollector(enabled=True)
    result = run_collection(db_path=tmp_path / "job.db", collectors=[collector_a, collector_b])
    assert result.failed_collectors == ["failing"]
    assert result.successful_collectors == ["fake"]


def test_stage6a_summary_counts_are_consistent(tmp_path):
    collector_a = FakeCollector(enabled=True, jobs=[_make_job("polymer engineer", source_job_id="a-1", posted_days=1)])
    collector_b = FakeCollector(enabled=True, jobs=[_make_job("software engineer", source_job_id="b-1", posted_days=1)])
    result = run_collection(db_path=tmp_path / "job.db", collectors=[collector_a, collector_b])
    assert result.raw_jobs_collected == 2
    assert result.relevant_jobs >= 1
    assert isinstance(result, CollectionRunSummary)


def test_stage6a_cli_main_runs_pipeline_without_email_or_scheduler(monkeypatch, tmp_path):
    from job_mentor import __main__ as cli

    calls = []

    def fake_run_collection(**kwargs):
        calls.append("ran")
        return CollectionRunSummary(
            run_started_at=datetime.now(timezone.utc),
            timezone_name="Europe/Berlin",
            collectors_attempted=1,
            collectors_skipped=0,
            successful_collectors=["fake"],
            failed_collectors=[],
            raw_jobs_collected=0,
            jobs_in_window=0,
            relevant_jobs=0,
            new_jobs=0,
            duplicates=0,
            below_threshold=0,
            invalid_jobs=0,
        )

    monkeypatch.setattr(cli.runner, "run_collection", fake_run_collection)
    cli.main(["--db", str(tmp_path / "cli.db"), "--collect-only"])
    assert calls == ["ran"]


def test_stage6a_uses_existing_matching_engine_and_date_filter():
    from job_mentor.matching.engine import MatchingEngine
    collector = FakeCollector(enabled=True, jobs=[_make_job("polymer engineer", posted_days=3)])
    result = run_collection(db_path="data/test_stage6a.db", collectors=[collector])
    assert result.relevant_jobs >= 1
    assert result.jobs_in_window >= 1
    assert hasattr(MatchingEngine, "score_job")


def test_stage6a_empty_collector_results_are_handled(tmp_path):
    result = run_collection(db_path=tmp_path / "job.db", collectors=[FakeCollector(enabled=True, jobs=[]), FakeCollector(enabled=False, jobs=[_make_job("polymer engineer")])])
    assert result.raw_jobs_collected == 0
    assert result.failed_collectors == []


def test_stage6a_no_real_network_calls_in_tests(monkeypatch):
    original = __import__("urllib.request", fromlist=["urlopen"])

    def fail(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(original, "urlopen", fail)
    from job_mentor.runner import discover_collectors
    assert discover_collectors() is not None
