from __future__ import annotations

import html
import ssl
import smtplib
from email.message import EmailMessage

from job_mentor.config.settings import load_settings
from job_mentor.reporting.text_renderer import render_daily_report_text


class EmailNotifier:
    """Email sender for job alerts using SMTP with TLS."""

    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_username: str | None = None,
        smtp_password: str | None = None,
        email_from: str | None = None,
        email_to: str | None = None,
        recipient_email: str | None = None,
        email_greeting: str | None = None,
        email_signoff: str | None = None,
    ):
        config = load_settings()
        self.smtp_host = (smtp_host or config.smtp_host or "").strip()
        self.smtp_port = int(smtp_port or config.smtp_port or 587)
        self.smtp_username = (smtp_username or config.smtp_username or "").strip()
        self.smtp_password = smtp_password or config.smtp_password or ""
        self.email_from = (email_from or config.email_from or "").strip()
        self.email_to = (email_to or recipient_email or config.email_to or "").strip()
        self.email_greeting = (email_greeting or config.email_greeting).strip() or "Hi there,"
        self.email_signoff = (email_signoff or config.email_signoff).strip() or "Best regards,"

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

    def _build_message(self, subject: str, plain_text: str, html_body: str | None = None, recipient: str | None = None) -> EmailMessage:
        recipient_email = (recipient or self.email_to).strip()
        if not recipient_email:
            raise ValueError("Recipient email is not configured. Set EMAIL_TO or pass recipient_email.")

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.email_from or "noreply@localhost"
        message["To"] = recipient_email
        message.set_content(plain_text)

        if html_body:
            message.add_alternative(html_body, subtype="html")
        return message

    def send(self, subject: str, body: str, *, html_body: str | None = None, recipient: str | None = None):
        missing = []
        if not self.smtp_host:
            missing.append("SMTP_HOST")
        if not self.email_from:
            missing.append("EMAIL_FROM")
        if not (recipient or self.email_to):
            missing.append("EMAIL_TO")
        if not self.smtp_username:
            missing.append("SMTP_USERNAME")
        if not self.smtp_password:
            missing.append("SMTP_PASSWORD")

        if missing:
            return {
                "status": "error",
                "error": "SMTP configuration is incomplete",
                "missing": missing,
                "recipient": recipient or self.email_to,
                "subject": subject,
            }

        message = self._build_message(subject, body, html_body=html_body, recipient=recipient)
        context = ssl.create_default_context()

        try:
            if self.smtp_port == 465:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=20)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20)
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()

            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            server.send_message(message)
            server.quit()
            return {
                "status": "success",
                "smtp_host": self.smtp_host,
                "smtp_port": self.smtp_port,
                "from": self.email_from,
                "to": recipient or self.email_to,
                "subject": subject,
                "message_id": message.get("Message-ID"),
            }
        except (smtplib.SMTPException, OSError, ValueError) as exc:
            return {
                "status": "error",
                "error": str(exc),
                "smtp_host": self.smtp_host,
                "smtp_port": self.smtp_port,
                "from": self.email_from,
                "to": recipient or self.email_to,
                "subject": subject,
            }
