class EmailNotifier:
    """Placeholder email sender for eventual job alerts."""

    def __init__(self, smtp_host: str | None = None, smtp_port: int | None = None, recipient_email: str | None = None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.recipient_email = recipient_email

    def send(self, subject: str, body: str):
        return {
            "status": "not_implemented",
            "recipient": self.recipient_email,
            "subject": subject,
            "body_preview": body[:80],
        }
