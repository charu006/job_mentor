from __future__ import annotations

from datetime import datetime, timedelta, timezone

from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.models.job import Job
from job_mentor.reporting.model import DailyReport, DailyReportJob
from job_mentor.reporting.service import DailyReportService
from job_mentor.reporting.text_renderer import render_daily_report_text
from job_mentor.timezone_utils import as_berlin


def _job(
    *,
    title: str,
    company: str | None = None,
    location: str | None = None,
    country: str = "Sweden",
    source: str = "arbetsformedlingen.se",
    source_job_id: str,
    url: str,
    posted_date=None,
    discovered_at: datetime | None = None,
    first_seen_at: datetime | None = None,
    match_score: float = 80.0,
    match_reasons: list[str] | None = None,
) -> Job:
    return Job(
        title=title,
        company=company,
        location=location,
        country=country,
        source=source,
        source_job_id=source_job_id,
        url=url,
        description="Polymer and elastomer materials.",
        posted_date=posted_date,
        discovered_at=discovered_at or datetime.now(timezone.utc),
        first_seen_at=first_seen_at or (discovered_at or datetime.now(timezone.utc)),
        last_seen_at=discovered_at or datetime.now(timezone.utc),
        match_score=match_score,
        match_reasons=match_reasons or ["polymer detected in title"],
    )


def test_report_retrieves_matching_jobs(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report.db"))
    repo.initialize_database()

    repo.insert_job(_job(title="Polymer Scientist", source_job_id="r1", url="https://example.com/r1", posted_date=datetime.now(timezone.utc) - timedelta(days=3)))
    repo.insert_job(_job(title="Old Role", source_job_id="r2", url="https://example.com/r2", posted_date=datetime.now(timezone.utc) - timedelta(days=30), match_score=90.0))
    repo.insert_job(_job(title="Low Score", source_job_id="r3", url="https://example.com/r3", posted_date=datetime.now(timezone.utc) - timedelta(days=2), match_score=35.0))

    report = DailyReportService(repository=repo).build_report(days=14)

    assert report.total_jobs == 1
    assert report.jobs[0].title == "Polymer Scientist"
    assert report.jobs[0].match_score >= 40


def test_jobs_below_threshold_are_excluded(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_low.db"))
    repo.initialize_database()
    repo.insert_job(_job(title="Too Low", source_job_id="low", url="https://example.com/low", posted_date=datetime.now(timezone.utc) - timedelta(days=1), match_score=39.0))

    report = DailyReportService(repository=repo).build_report(days=14)
    assert report.total_jobs == 0
    assert report.jobs == []


def test_jobs_outside_the_window_are_excluded(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_window.db"))
    repo.initialize_database()
    repo.insert_job(_job(title="Too Old", source_job_id="old", url="https://example.com/old", posted_date=datetime.now(timezone.utc) - timedelta(days=20), match_score=95.0))

    report = DailyReportService(repository=repo).build_report(days=14)
    assert report.total_jobs == 0


def test_newest_posted_jobs_sort_first(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_sort.db"))
    repo.initialize_database()

    repo.insert_job(_job(title="Oldest", source_job_id="s1", url="https://example.com/s1", posted_date=datetime.now(timezone.utc) - timedelta(days=10), match_score=85.0))
    repo.insert_job(_job(title="Newest", source_job_id="s2", url="https://example.com/s2", posted_date=datetime.now(timezone.utc) - timedelta(days=1), match_score=85.0))
    repo.insert_job(_job(title="Middle", source_job_id="s3", url="https://example.com/s3", posted_date=datetime.now(timezone.utc) - timedelta(days=4), match_score=85.0))

    report = DailyReportService(repository=repo).build_report(days=14)
    assert [job.title for job in report.jobs] == ["Newest", "Middle", "Oldest"]


def test_missing_posted_date_uses_discovered_or_first_seen_for_ordering(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_order.db"))
    repo.initialize_database()

    now = datetime.now(timezone.utc)
    repo.insert_job(_job(title="Fallback First", source_job_id="f1", url="https://example.com/f1", posted_date=None, discovered_at=now - timedelta(days=2), first_seen_at=now - timedelta(days=2), match_score=90.0))
    repo.insert_job(_job(title="Fallback Second", source_job_id="f2", url="https://example.com/f2", posted_date=None, discovered_at=now - timedelta(days=5), first_seen_at=now - timedelta(days=5), match_score=90.0))

    report = DailyReportService(repository=repo).build_report(days=14)
    assert [job.title for job in report.jobs] == ["Fallback First", "Fallback Second"]


def test_berlin_report_date_and_timezone_are_used(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_berlin.db"))
    repo.initialize_database()
    repo.insert_job(_job(title="Berlin Job", source_job_id="b1", url="https://example.com/b1", posted_date=datetime.now(timezone.utc) - timedelta(days=1), match_score=80.0))

    report = DailyReportService(repository=repo).build_report(days=14)
    assert report.timezone == "Europe/Berlin"
    assert report.report_date == as_berlin(datetime.now(timezone.utc)).date().isoformat()


def test_empty_report_and_plain_text_rendering(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_empty.db"))
    repo.initialize_database()

    report = DailyReportService(repository=repo).build_report(days=14)
    assert report.total_jobs == 0
    assert report.jobs == []
    text = render_daily_report_text(report)
    assert "No matching jobs found in the last 14 days." in text


def test_plain_text_render_includes_required_fields(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_render.db"))
    repo.initialize_database()
    repo.insert_job(
        _job(
            title="R&D Engineer in Polymer Materials",
            company="NKT HV Cables AB",
            location="Stockholm",
            country="Sweden",
            source="Arbetsförmedlingen",
            source_job_id="r4",
            url="https://example.com/r4",
            posted_date=datetime(2026, 9, 16, 15, 25, 2, tzinfo=timezone.utc),
            match_score=83.16,
            match_reasons=["polymer detected in title", "elastomer/rubber context detected in description"],
        )
    )

    report = DailyReportService(repository=repo).build_report(days=14)
    text = render_daily_report_text(report)
    assert "JOB MENTOR — DAILY JOB REPORT" in text
    assert "R&D Engineer in Polymer Materials" in text
    assert "Company: NKT HV Cables AB" in text
    assert "Posted: 16 Sep 2026" in text
    assert "Match score: 83.16" in text
    assert "Why it matched:" in text


def test_structured_output_contains_required_fields(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_structured.db"))
    repo.initialize_database()
    repo.insert_job(_job(title="Structured Job", source_job_id="s5", url="https://example.com/s5", posted_date=datetime.now(timezone.utc) - timedelta(days=2), match_score=72.0))

    report = DailyReportService(repository=repo).build_report(days=14)
    assert isinstance(report, DailyReport)
    assert isinstance(report.jobs[0], DailyReportJob)
    payload = report.as_dict()
    assert "report_date" in payload
    assert "generated_at" in payload
    assert "timezone" in payload
    assert "search_window_days" in payload
    assert "jobs" in payload
    assert "total_jobs" in payload
    assert payload["total_jobs"] == 1
    assert list(report.jobs[0].as_dict().keys()) == [
        "title",
        "company",
        "location",
        "country",
        "source",
        "url",
        "posted_date",
        "match_score",
        "match_reasons",
    ]


def test_report_ordering_is_deterministic(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "report_deterministic.db"))
    repo.initialize_database()
    repo.insert_job(_job(title="A", source_job_id="d1", url="https://example.com/d1", posted_date=datetime.now(timezone.utc) - timedelta(days=2), match_score=80.0))
    repo.insert_job(_job(title="B", source_job_id="d2", url="https://example.com/d2", posted_date=datetime.now(timezone.utc) - timedelta(days=2), match_score=80.0))

    report = DailyReportService(repository=repo).build_report(days=14)
    assert [job.title for job in report.jobs] == ["A", "B"]
