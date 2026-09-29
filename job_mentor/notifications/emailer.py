from __future__ import annotations

import html

from job_mentor.config.settings import settings
from job_mentor.reporting.text_renderer import render_daily_report_text


class EmailNotifier:
    """Placeholder email sender for eventual job alerts."""

    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        recipient_email: str | None = None,
        email_greeting: str | None = None,
        email_signoff: str | None = None,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.recipient_email = recipient_email
        self.email_greeting = (email_greeting or settings.email_greeting).strip() or "Hi there,"
        self.email_signoff = (email_signoff or settings.email_signoff).strip() or "Best regards,"

    def _normalize_report_body(self, report_or_text: object) -> str:
        if isinstance(report_or_text, str):
            return report_or_text.strip()
        if hasattr(report_or_text, "jobs") or hasattr(report_or_text, "report_date"):
            return render_daily_report_text(report_or_text).strip()
        return str(report_or_text).strip()

    def render_plain_text(self, report_or_text: object) -> str:
        body = self._normalize_report_body(report_or_text)
        if not body:
            return f"{self.email_greeting}\n\n{self.email_signoff}"
        return f"{self.email_greeting}\n\n{body}\n\n{self.email_signoff}"

    def render_html(self, report_or_text: object) -> str:
        body = self._normalize_report_body(report_or_text)
        greeting = html.escape(self.email_greeting)
        signoff = html.escape(self.email_signoff)
        if not body:
            return f"<p>{greeting}</p><p>{signoff}</p>"

        escaped_body = html.escape(body).replace("\n\n", "</p><p>").replace("\n", "<br>")
        return f"<p>{greeting}</p><p>{escaped_body}</p><p>{signoff}</p>"

    def send(self, subject: str, body: str):
        return {
            "status": "not_implemented",
            "recipient": self.recipient_email,
            "subject": subject,
            "body_preview": body[:80],
        }
