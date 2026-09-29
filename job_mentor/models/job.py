from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime | date | str | None) -> datetime | date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                parsed = datetime.combine(date.fromisoformat(value), time.min, tzinfo=timezone.utc)
            except ValueError:
                return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    return value


@dataclass
class Job:
    title: str | None = None
    company: str | None = None
    location: str | None = None
    country: str | None = None
    source: str | None = None
    source_job_id: str | None = None
    url: str | None = None
    description: str | None = None
    posted_date: date | datetime | str | None = None
    discovered_at: datetime | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    notified_at: datetime | None = None
    match_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)
    status: str = "new"
    id: int | None = None
    canonical_url: str | None = None
    fingerprint: str | None = None

    def __post_init__(self):
        if self.discovered_at is None:
            self.discovered_at = utc_now()
        if self.first_seen_at is None:
            self.first_seen_at = self.discovered_at
        if self.last_seen_at is None:
            self.last_seen_at = self.discovered_at

        self.discovered_at = ensure_utc(self.discovered_at)
        self.first_seen_at = ensure_utc(self.first_seen_at)
        self.last_seen_at = ensure_utc(self.last_seen_at)
        self.notified_at = ensure_utc(self.notified_at)
        self.posted_date = ensure_utc(self.posted_date) or self.posted_date

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "country": self.country,
            "source": self.source,
            "source_job_id": self.source_job_id,
            "url": self.url,
            "description": self.description,
            "posted_date": self.posted_date.isoformat() if isinstance(self.posted_date, (date, datetime)) else self.posted_date,
            "discovered_at": self.discovered_at.isoformat() if self.discovered_at else None,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "notified_at": self.notified_at.isoformat() if self.notified_at else None,
            "match_score": self.match_score,
            "match_reasons": ";".join(self.match_reasons),
            "status": self.status,
            "canonical_url": self.canonical_url,
            "fingerprint": self.fingerprint,
        }
