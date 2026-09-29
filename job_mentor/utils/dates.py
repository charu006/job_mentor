from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone


def normalize_datetime(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            try:
                parsed_date = date.fromisoformat(text)
                return datetime.combine(parsed_date, time.min, tzinfo=timezone.utc)
            except ValueError:
                return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    return None


def is_within_search_window(posted_date, days: int = 14) -> bool:
    if posted_date is None:
        return False

    now_utc = datetime.now(timezone.utc)

    if isinstance(posted_date, datetime):
        parsed = normalize_datetime(posted_date)
        if parsed is None:
            return False
        if parsed > now_utc:
            return False
        cutoff = now_utc - timedelta(days=days)
        return parsed >= cutoff

    if isinstance(posted_date, date):
        if posted_date > now_utc.date():
            return False
        cutoff_date = (now_utc - timedelta(days=days)).date()
        return posted_date >= cutoff_date

    if isinstance(posted_date, str):
        text = posted_date.strip()
        if not text:
            return False
        try:
            parsed_date = date.fromisoformat(text)
        except ValueError:
            parsed = normalize_datetime(text)
            if parsed is None:
                return False
            if parsed > now_utc:
                return False
            cutoff = now_utc - timedelta(days=days)
            return parsed >= cutoff
        if parsed_date > now_utc.date():
            return False
        cutoff_date = (now_utc - timedelta(days=days)).date()
        return parsed_date >= cutoff_date

    return False


def is_recent_posting(posted_at: datetime | str | date | None, days: int = 14) -> bool:
    return is_within_search_window(posted_at, days=days)
