from __future__ import annotations

from pathlib import Path


def test_stage7a_github_actions_workflow_uses_native_berlin_schedule_and_manual_dispatch():
    workflow_path = Path(".github/workflows/job-mentor-daily.yml")
    workflow = workflow_path.read_text(encoding="utf-8")

    assert 'cron: "7 12 * * *"' in workflow
    assert 'timezone: "Europe/Berlin"' in workflow
    assert "workflow_dispatch:" in workflow
    assert 'default: true' in workflow
    assert "python -m job_mentor" in workflow
    assert "--dry-run" in workflow
    assert "Determine whether the Berlin schedule is due" not in workflow
    assert "default_scheduler.is_due" not in workflow

    for secret_name in ["SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"]:
        assert f"${{{{ secrets.{secret_name} }}}}" in workflow


def test_stage7a_manual_dispatch_dry_run_and_real_commands_are_preserved():
    workflow = Path(".github/workflows/job-mentor-daily.yml").read_text(encoding="utf-8")

    assert 'if [ "${{ github.event_name }}" = "workflow_dispatch" ] && [ "${{ inputs.dry_run }}" = "true" ]; then' in workflow
    assert 'echo "command=python -m job_mentor --dry-run" >> "$GITHUB_OUTPUT"' in workflow
    assert 'echo "command=python -m job_mentor" >> "$GITHUB_OUTPUT"' in workflow