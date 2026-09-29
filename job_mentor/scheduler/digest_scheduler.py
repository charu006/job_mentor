from __future__ import annotations

from datetime import datetime, timedelta

from job_mentor.config.settings import settings
from job_mentor.timezone_utils import as_berlin, utc_now


class DailyDigestScheduler:
    """Schedule abstraction for the future daily digest delivery window."""

    def __init__(self, timezone_name: str = "Europe/Berlin", report_hour: int = 12, report_minute: int = 0):
        self.timezone_name = timezone_name
        self.report_hour = report_hour
        self.report_minute = report_minute

    def is_due(self, now_utc: datetime | None = None) -> bool:
        now = as_berlin(now_utc or utc_now())
        return now.hour == self.report_hour and now.minute == self.report_minute

    def next_run(self, now_utc: datetime | None = None) -> datetime:
        now = now_utc or utc_now()
        local_now = as_berlin(now)
        target = local_now.replace(hour=self.report_hour, minute=self.report_minute, second=0, microsecond=0)
        if local_now >= target:
            target += timedelta(days=1)
        return target.astimezone(now.tzinfo or now.astimezone().tzinfo)


default_scheduler = DailyDigestScheduler(
    timezone_name=settings.timezone,
    report_hour=settings.report_hour,
    report_minute=settings.report_minute,
)
