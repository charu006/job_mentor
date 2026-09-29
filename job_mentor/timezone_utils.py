from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BERLIN_TIMEZONE = ZoneInfo("Europe/Berlin")


def as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def as_berlin(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    utc_value = as_utc(value)
    return utc_value.astimezone(BERLIN_TIMEZONE)


def germany_now() -> datetime:
    return datetime.now(BERLIN_TIMEZONE)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def germany_date_string(value: datetime | None = None) -> str:
    now = as_berlin(value or utc_now())
    return now.date().isoformat()


def is_report_time(now_utc: datetime | None = None, report_hour: int = 12, report_minute: int = 0) -> bool:
    now = as_berlin(now_utc or utc_now())
    return now.hour == report_hour and now.minute == report_minute
