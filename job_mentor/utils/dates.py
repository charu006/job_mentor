from __future__ import annotations

from datetime import datetime, timedelta


def is_recent_posting(posted_at: datetime | str, days: int = 14) -> bool:
    if isinstance(posted_at, str):
        try:
            posted_at = datetime.fromisoformat(posted_at)
        except ValueError:
            return False

    if not isinstance(posted_at, datetime):
        return False

    cutoff = datetime.utcnow() - timedelta(days=days)
    return posted_at >= cutoff
