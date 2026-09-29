from __future__ import annotations

from datetime import datetime, timezone

import pytest

from job_mentor.config.settings import load_settings
from job_mentor.reporting.model import DailyReport, DailyReportJob
from job_mentor.runner import CollectionRunSummary
from job_mentor.timezone_utils import germany_date_string
from job_mentor.workflow import WorkflowResult, run_job_mentor_workflow


def _summary() -> CollectionRunSummary:
    return CollectionRunSummary(
        run_started_at=datetime.now(timezone.utc),
        timezone_name="Europe/Berlin",
        collectors_attempted=1,
        collectors_skipped=0,
        successful_collectors=["fake"],
        failed_collectors=[],
        raw_jobs_collected=1,
        jobs_in_window=1,
        relevant_jobs=1,
        new_jobs=1,
        duplicates=0,
        below_threshold=0,
        invalid_jobs=0,
    )


def _report(report_date: str | None = None) -> DailyReport:
    return DailyReport(
        report_date=report_date or germany_date_string(),
        timezone="Europe/Berlin",
        generated_at=datetime.now(timezone.utc),
        search_window_days=14,
        jobs=[
            DailyReportJob(
                title="Polymer Engineer",
                company="Acme",
                location="Berlin",
                country="Germany",
                source="fake",
                url="https://example.com/job",
                posted_date=datetime.now(timezone.utc),
                match_score=91.5,
                match_reasons=["polymer detected in title"],
            )
        ],
    )


def test_stage6d_end_to_end_workflow_with_mocked_boundaries(tmp_path, monkeypatch):
    calls = {}

    def fake_collection_runner(**kwargs):
        calls["collection_runner"] = kwargs
        return _summary()

    class FakeReportService:
        def __init__(self, repository):
            calls["repository"] = repository

        def build_report(self, days):
            calls["build_report_days"] = days
            return _report()

    class FakeNotifier:
        def __init__(self, **kwargs):
            calls["notifier_init"] = kwargs
            self.email_to = kwargs.get("email_to")

        def render_plain_text(self, report):
            calls["plain_report"] = report
            return "PLAIN BODY"

        def render_html(self, report):
            calls["html_report"] = report
            return "<p>HTML BODY</p>"

        def send(self, subject, body, *, html_body=None, recipient=None):
            calls["send"] = {
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "recipient": recipient,
            }
            return {"status": "success", "subject": subject, "recipient": recipient}

    monkeypatch.setattr("job_mentor.workflow.run_collection", fake_collection_runner)
    monkeypatch.setattr("job_mentor.workflow.DailyReportService", FakeReportService)
    monkeypatch.setattr("job_mentor.workflow.EmailNotifier", FakeNotifier)

    result = run_job_mentor_workflow(db_path=tmp_path / "workflow.db", days=7)

    assert calls["collection_runner"]["db_path"] == tmp_path / "workflow.db"
    assert calls["collection_runner"]["days"] == 7
    assert calls["build_report_days"] == 7
    assert calls["send"]["subject"] == f"JOB MENTOR — DAILY JOB REPORT ({result.report.report_date})"
    assert calls["send"]["body"] == "PLAIN BODY"
    assert calls["send"]["html_body"] == "<p>HTML BODY</p>"
    assert calls["send"]["recipient"] == result.email.recipient
    assert result.notification_result == {"status": "success", "subject": calls["send"]["subject"], "recipient": result.email.recipient}
    assert result.email.plain_text == "PLAIN BODY"


def test_stage6d_dry_run_never_calls_smtp(tmp_path, monkeypatch):
    calls = {"send": 0}

    def fake_collection_runner(**kwargs):
        return _summary()

    class FakeReportService:
        def __init__(self, repository):
            self.repository = repository

        def build_report(self, days):
            return _report()

    class FakeNotifier:
        def __init__(self, **kwargs):
            self.email_to = kwargs.get("email_to") or "alerts@example.com"

        def render_plain_text(self, report):
            return "Hi Jannu,\n\nDaily report body\n\nYour potato 🥔"

        def render_html(self, report):
            return "<p>Hi Jannu,</p><p>Daily report body</p><p>Your potato 🥔</p>"

        def send(self, *args, **kwargs):
            calls["send"] += 1
            raise AssertionError("SMTP should not be called in dry-run mode")

    monkeypatch.setattr("job_mentor.workflow.run_collection", fake_collection_runner)
    monkeypatch.setattr("job_mentor.workflow.DailyReportService", FakeReportService)
    monkeypatch.setattr("job_mentor.workflow.EmailNotifier", FakeNotifier)

    result = run_job_mentor_workflow(db_path=tmp_path / "dry-run.db", dry_run=True)

    assert calls["send"] == 0
    assert result.dry_run is True
    assert result.notification_result is None
    assert result.email.recipient == result.settings.email_to
    assert result.email.subject == f"JOB MENTOR — DAILY JOB REPORT ({result.report.report_date})"
    assert "Daily report body" in result.email.plain_text


def test_stage6d_cli_dry_run_prints_expected_preview(tmp_path, monkeypatch, capsys):
    from job_mentor import __main__ as cli

    result = WorkflowResult(
        settings=load_settings(),
        collection_summary=_summary(),
        report=_report("2026-09-30"),
        email=type(
            "EmailPreview",
            (),
            {
                "recipient": "alerts@example.com",
                "subject": "JOB MENTOR — DAILY JOB REPORT (2026-09-30)",
                "plain_text": "Hi Jannu,\n\nDaily report body\n\nYour potato 🥔",
                "html_body": "<p>Hi Jannu,</p><p>Daily report body</p><p>Your potato 🥔</p>",
            },
        )(),
        notification_result=None,
        dry_run=True,
    )

    monkeypatch.setattr(cli, "run_job_mentor_workflow", lambda **kwargs: result)

    cli.main(["--dry-run", "--db", str(tmp_path / "cli.db")])
    output = capsys.readouterr().out

    assert "Dry run preview:" in output
    assert "Recipient: alerts@example.com" in output
    assert "Subject: JOB MENTOR — DAILY JOB REPORT (2026-09-30)" in output
    assert "Daily report body" in output


def test_stage6d_normal_mode_invokes_notifier(tmp_path, monkeypatch):
    calls = {}

    def fake_collection_runner(**kwargs):
        return _summary()

    class FakeReportService:
        def __init__(self, repository):
            self.repository = repository

        def build_report(self, days):
            return _report()

    class FakeNotifier:
        def __init__(self, **kwargs):
            self.email_to = kwargs.get("email_to") or "alerts@example.com"

        def render_plain_text(self, report):
            return "BODY"

        def render_html(self, report):
            return "<p>BODY</p>"

        def send(self, subject, body, *, html_body=None, recipient=None):
            calls["send"] = {
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "recipient": recipient,
            }
            return {"status": "success"}

    monkeypatch.setattr("job_mentor.workflow.run_collection", fake_collection_runner)
    monkeypatch.setattr("job_mentor.workflow.DailyReportService", FakeReportService)
    monkeypatch.setattr("job_mentor.workflow.EmailNotifier", FakeNotifier)

    result = run_job_mentor_workflow(db_path=tmp_path / "normal.db", days=14)

    assert calls["send"]["subject"].startswith("JOB MENTOR — DAILY JOB REPORT")
    assert calls["send"]["body"] == "BODY"
    assert result.notification_result == {"status": "success"}


def test_stage6d_report_errors_are_surfaced(tmp_path, monkeypatch):
    def fake_collection_runner(**kwargs):
        return _summary()

    class FailingReportService:
        def __init__(self, repository):
            self.repository = repository

        def build_report(self, days):
            raise ValueError("report boom")

    monkeypatch.setattr("job_mentor.workflow.run_collection", fake_collection_runner)
    monkeypatch.setattr("job_mentor.workflow.DailyReportService", FailingReportService)

    with pytest.raises(ValueError, match="report boom"):
        run_job_mentor_workflow(db_path=tmp_path / "failing.db")


def test_stage6d_smtp_errors_are_surfaced(tmp_path, monkeypatch):
    def fake_collection_runner(**kwargs):
        return _summary()

    class FakeReportService:
        def __init__(self, repository):
            self.repository = repository

        def build_report(self, days):
            return _report()

    class FailingNotifier:
        def __init__(self, **kwargs):
            self.email_to = kwargs.get("email_to") or "alerts@example.com"

        def render_plain_text(self, report):
            return "BODY"

        def render_html(self, report):
            return "<p>BODY</p>"

        def send(self, *args, **kwargs):
            return {"status": "error", "error": "smtp failed"}

    monkeypatch.setattr("job_mentor.workflow.run_collection", fake_collection_runner)
    monkeypatch.setattr("job_mentor.workflow.DailyReportService", FakeReportService)
    monkeypatch.setattr("job_mentor.workflow.EmailNotifier", FailingNotifier)

    with pytest.raises(RuntimeError, match="SMTP delivery failed: smtp failed"):
        run_job_mentor_workflow(db_path=tmp_path / "smtp-fail.db")


def test_stage6d_preserves_europe_berlin_report_date(tmp_path, monkeypatch):
    def fake_collection_runner(**kwargs):
        return _summary()

    class FakeReportService:
        def __init__(self, repository):
            self.repository = repository

        def build_report(self, days):
            return DailyReport(
                report_date=germany_date_string(),
                timezone="Europe/Berlin",
                generated_at=datetime.now(timezone.utc),
                search_window_days=days,
                jobs=[],
            )

    class FakeNotifier:
        def __init__(self, **kwargs):
            self.email_to = kwargs.get("email_to") or "alerts@example.com"

        def render_plain_text(self, report):
            return "BODY"

        def render_html(self, report):
            return "<p>BODY</p>"

        def send(self, subject, body, *, html_body=None, recipient=None):
            return {"status": "success"}

    monkeypatch.setattr("job_mentor.workflow.run_collection", fake_collection_runner)
    monkeypatch.setattr("job_mentor.workflow.DailyReportService", FakeReportService)
    monkeypatch.setattr("job_mentor.workflow.EmailNotifier", FakeNotifier)

    result = run_job_mentor_workflow(db_path=tmp_path / "berlin.db")

    assert result.report.timezone == "Europe/Berlin"
    assert result.report.report_date == germany_date_string()