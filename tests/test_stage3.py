from datetime import datetime, timedelta, timezone

from job_mentor.collectors.arbeitsagentur import ArbeitsagenturCollector
from job_mentor.config.settings import settings
from job_mentor.core.pipeline import collect_jobs_for_window
from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.models.job import Job
from job_mentor.reporting.service import DailyReportService
from job_mentor.timezone_utils import as_berlin, germany_date_string, is_report_time
from job_mentor.utils.dates import is_within_search_window


def test_berlin_configuration_is_applied():
    assert settings.timezone == "Europe/Berlin"
    assert settings.report_hour == 12
    assert settings.report_minute == 0


def test_utc_to_berlin_handles_cet_and_cest():
    cet = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
    cest = datetime(2024, 7, 15, 12, 0, tzinfo=timezone.utc)

    assert as_berlin(cet).tzname() == "CET"
    assert as_berlin(cest).tzname() == "CEST"


def test_schedule_uses_germany_time():
    berlin_eleven = datetime(2024, 7, 15, 9, 0, tzinfo=timezone.utc)
    berlin_noon = datetime(2024, 7, 15, 10, 0, tzinfo=timezone.utc)

    assert is_report_time(berlin_eleven, report_hour=12, report_minute=0) is False
    assert is_report_time(berlin_noon, report_hour=12, report_minute=0) is True


def test_collector_instantiation_and_normalization():
    collector = ArbeitsagenturCollector(search_terms=["elastomer"])
    assert collector.source_name == "jobs.arbeitsagentur.de"
    assert "elastomer" in collector.search_terms

    raw_job = {
        "title": "Werkstoffentwickler Elastomer",
        "company": "RubberTech GmbH",
        "location": "Berlin",
        "id": "A-900",
        "url": "https://jobs.arbeitsagentur.de/position/900",
        "date": "2026-09-25",
        "description": "Develop elastomer applications and formulations.",
    }

    normalized = collector.normalize_raw_job(raw_job)
    assert isinstance(normalized, Job)
    assert normalized.title == "Werkstoffentwickler Elastomer"
    assert normalized.country == "Germany"
    assert normalized.source == "jobs.arbeitsagentur.de"


def test_14_day_filter_and_future_dates_are_handled():
    recent = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    old = (datetime.now(timezone.utc) - timedelta(days=15)).date().isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()

    assert is_within_search_window(recent, days=14) is True
    assert is_within_search_window(old, days=14) is False
    assert is_within_search_window(future, days=14) is False
    assert is_within_search_window(None, days=14) is False
    assert is_within_search_window("not-a-date", days=14) is False


def test_collection_pipeline_stores_and_updates_jobs(tmp_path, monkeypatch):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    collector = ArbeitsagenturCollector(search_terms=["elastomer"])

    sample_jobs = [{
        "title": "Elastomer Development Engineer",
        "company": "Polymer Solutions GmbH",
        "location": "Berlin",
        "id": "portal-01",
        "url": "https://jobs.arbeitsagentur.de/position/portal-01?utm_source=test",
        "date": (datetime.now(timezone.utc) - timedelta(days=4)).date().isoformat(),
        "description": "Develop elastomer compounds and formulations.",
    }]

    monkeypatch.setattr(collector, "fetch_raw_jobs", lambda term: sample_jobs)
    stored = collect_jobs_for_window(collector, repo, terms=["elastomer"], days=14)
    assert len(stored) == 1
    assert repo.get_job_by_source_and_job_id("jobs.arbeitsagentur.de", "portal-01") is not None

    first_seen = repo.get_job_by_source_and_job_id("jobs.arbeitsagentur.de", "portal-01").first_seen_at
    updated_payload = [{
        "title": "Elastomer Development Engineer",
        "company": "Polymer Solutions GmbH",
        "location": "Berlin",
        "id": "portal-01",
        "url": "https://jobs.arbeitsagentur.de/position/portal-01",
        "date": (datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat(),
        "description": "Updated elastomer development role.",
    }]
    monkeypatch.setattr(collector, "fetch_raw_jobs", lambda term: updated_payload)
    second_run = collect_jobs_for_window(collector, repo, terms=["elastomer"], days=14)
    assert len(second_run) == 1
    same = repo.get_job_by_source_and_job_id("jobs.arbeitsagentur.de", "portal-01")
    assert same.first_seen_at == first_seen
    assert same.last_seen_at is not None


def test_daily_report_service_returns_structured_data(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()

    recent_job = Job(
        title="Polymer Scientist",
        company="Materials Lab GmbH",
        location="Dresden",
        country="Germany",
        source="jobs.arbeitsagentur.de",
        source_job_id="report-001",
        url="https://jobs.arbeitsagentur.de/report-001",
        description="Polymer science role.",
        posted_date=(datetime.now(timezone.utc) - timedelta(days=5)).date().isoformat(),
        discovered_at=datetime.now(timezone.utc),
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
        match_score=80.0,
        match_reasons=["polymer detected in title"],
    )
    repo.insert_job(recent_job)

    service = DailyReportService(repository=repo)
    initial_report = service.get_initial_report(report_date=germany_date_string(), days=14)
    assert initial_report.timezone == "Europe/Berlin"
    assert initial_report.total_jobs >= 1

    initial_report.jobs[0].notified_at = datetime.now(timezone.utc)
    repo.update_job(initial_report.jobs[0])

    subsequent_report = service.get_daily_report(report_date=germany_date_string(), days=14)
    assert subsequent_report.jobs == []

    empty_repo = SQLiteJobRepository(db_path=str(tmp_path / "empty.db"))
    empty_repo.initialize_database()
    empty_report = DailyReportService(repository=empty_repo).get_daily_report(report_date=germany_date_string(), days=14)
    assert empty_report.jobs == []
    assert empty_report.total_jobs == 0
