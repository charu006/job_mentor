from __future__ import annotations

from datetime import date, datetime

from job_mentor.reporting.model import DailyReport
from job_mentor.timezone_utils import as_berlin


def _format_display_date(value: date | datetime | str | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return "N/A"
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                return value
        return _format_display_date(parsed)
    if isinstance(value, datetime):
        berlin_value = as_berlin(value)
        return berlin_value.strftime("%d %b %Y")
    if isinstance(value, date):
        berlin_value = as_berlin(datetime.combine(value, datetime.min.time()))
        return berlin_value.strftime("%d %b %Y")
    return str(value)


def render_daily_report_text(report: DailyReport) -> str:
    report_date = report.report_date or "N/A"
    lines: list[str] = [
        "JOB MENTOR — DAILY JOB REPORT",
        f"Date: {datetime.strptime(report_date, '%Y-%m-%d').strftime('%d %B %Y') if report_date else 'N/A'}",
        f"Timezone: {report.timezone}",
        f"Search window: {report.search_window_days} days",
        f"Matching jobs: {report.total_jobs}",
        "",
    ]

    if report.total_jobs == 0:
        lines.append(f"No matching jobs found in the last {report.search_window_days} days.")
        return "\n".join(lines) + "\n"

    for index, job in enumerate(report.jobs, start=1):
        lines.append(f"{index}. {job.title or 'Untitled job'}")
        if job.company:
            lines.append(f"   Company: {job.company}")
        if job.location:
            lines.append(f"   Location: {job.location}")
        if job.country:
            lines.append(f"   Country: {job.country}")
        if job.source:
            lines.append(f"   Source: {job.source}")
        if job.posted_date:
            lines.append(f"   Posted: {_format_display_date(job.posted_date)}")
        lines.append(f"   Match score: {float(job.match_score):.2f}")
        if job.match_reasons:
            lines.append("   Why it matched:")
            for reason in job.match_reasons:
                lines.append(f"   - {reason}")
        if job.url:
            lines.append(f"   URL: {job.url}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
