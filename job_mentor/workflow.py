from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from job_mentor.collectors.base import BaseCollector
from job_mentor.config.settings import AppSettings, load_settings
from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.notifications.emailer import EmailNotifier
from job_mentor.reporting.model import DailyReport
from job_mentor.reporting.service import DailyReportService
from job_mentor.runner import CollectionRunSummary, run_collection


DEFAULT_DAILY_REPORT_SUBJECT = "JOB MENTOR — DAILY JOB REPORT"


@dataclass(frozen=True)
class RenderedEmail:
    recipient: str
    subject: str
    plain_text: str
    html_body: str


@dataclass(frozen=True)
class WorkflowResult:
    settings: AppSettings
    collection_summary: CollectionRunSummary
    report: DailyReport
    email: RenderedEmail
    notification_result: dict[str, Any] | None
    dry_run: bool


def _build_email(report: DailyReport, notifier: EmailNotifier, recipient: str) -> RenderedEmail:
    subject = f"{DEFAULT_DAILY_REPORT_SUBJECT} ({report.report_date})"
    plain_text = notifier.render_plain_text(report)
    html_body = notifier.render_html(report)
    return RenderedEmail(recipient=recipient, subject=subject, plain_text=plain_text, html_body=html_body)


def run_job_mentor_workflow(
    *,
    db_path: str | Path | None = None,
    days: int | None = None,
    dry_run: bool = False,
    collectors: Iterable[BaseCollector] | None = None,
    settings_loader: Callable[[], AppSettings] | None = None,
    collection_runner: Callable[..., CollectionRunSummary] | None = None,
    repository_factory: Callable[[str | Path | None], SQLiteJobRepository] | None = None,
    report_service_factory: Callable[[SQLiteJobRepository], DailyReportService] | None = None,
    notifier_factory: Callable[..., EmailNotifier] | None = None,
) -> WorkflowResult:
    settings_loader = settings_loader or load_settings
    collection_runner = collection_runner or run_collection
    repository_factory = repository_factory or SQLiteJobRepository
    report_service_factory = report_service_factory or DailyReportService
    notifier_factory = notifier_factory or EmailNotifier

    settings = settings_loader()
    effective_db_path: str | Path | None = db_path or settings.database_path
    effective_days = days if days is not None else settings.search_window_days

    collection_summary = collection_runner(db_path=effective_db_path, collectors=collectors, days=effective_days)

    repository = repository_factory(effective_db_path)
    report_service = report_service_factory(repository=repository)
    report = report_service.build_report(days=effective_days)

    notifier = notifier_factory(
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_username=settings.smtp_username,
        smtp_password=settings.smtp_password,
        email_from=settings.email_from,
        email_to=settings.email_to or settings.recipient_email,
        email_greeting=settings.email_greeting,
        email_signoff=settings.email_signoff,
    )
    recipient = getattr(notifier, "email_to", None) or settings.email_to or settings.recipient_email or ""
    email = _build_email(report, notifier, recipient)

    if dry_run:
        return WorkflowResult(
            settings=settings,
            collection_summary=collection_summary,
            report=report,
            email=email,
            notification_result=None,
            dry_run=True,
        )

    notification_result = notifier.send(
        email.subject,
        email.plain_text,
        html_body=email.html_body,
        recipient=recipient,
    )
    if notification_result.get("status") != "success":
        error_message = notification_result.get("error", "SMTP delivery failed")
        raise RuntimeError(f"SMTP delivery failed: {error_message}")

    return WorkflowResult(
        settings=settings,
        collection_summary=collection_summary,
        report=report,
        email=email,
        notification_result=notification_result,
        dry_run=False,
    )