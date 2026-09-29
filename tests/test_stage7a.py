from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from job_mentor.scheduler.digest_scheduler import DailyDigestScheduler, default_scheduler
from job_mentor.timezone_utils import as_berlin


def test_stage7a_github_actions_workflow_uses_dual_crons_and_manual_dispatch():
    workflow_path = Path(".github/workflows/job-mentor-daily.yml")
    workflow = workflow_path.read_text(encoding="utf-8")

    assert 'cron: "0 10 * * *"' in workflow
    assert 'cron: "0 11 * * *"' in workflow
    assert "workflow_dispatch:" in workflow
    assert 'default: true' in workflow
    assert "python -m job_mentor" in workflow
    assert "--dry-run" in workflow

    for secret_name in ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"]:
        assert f"${{{{ secrets.{secret_name} }}}}" in workflow


def test_stage7a_scheduler_keeps_berlin_noon_across_dst():
    scheduler = DailyDigestScheduler(report_hour=12, report_minute=0)

    winter_noon_utc = datetime(2026, 1, 15, 11, 0, tzinfo=timezone.utc)
    summer_noon_utc = datetime(2026, 7, 15, 10, 0, tzinfo=timezone.utc)

    assert scheduler.timezone_name == "Europe/Berlin"
    assert default_scheduler.timezone_name == "Europe/Berlin"
    assert scheduler.is_due(winter_noon_utc) is True
    assert scheduler.is_due(summer_noon_utc) is True
    assert as_berlin(winter_noon_utc).hour == 12
    assert as_berlin(summer_noon_utc).hour == 12
    assert scheduler.is_due(datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)) is False
    assert scheduler.is_due(datetime(2026, 7, 15, 11, 0, tzinfo=timezone.utc)) is False