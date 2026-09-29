from __future__ import annotations

import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from job_mentor.config.settings import settings
from job_mentor.models.job import Job


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def canonicalize_url(raw_url: str | None) -> str:
    if not raw_url:
        return ""
    value = raw_url.strip()
    if not value:
        return ""

    parsed = urlsplit(value)
    query_items = []
    for key, val in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower().startswith("utm_") or key.lower() in {"gclid", "fbclid", "mc_cid", "mc_eid", "msclkid"}:
            continue
        query_items.append((key, val))

    cleaned = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        path=parsed.path.rstrip("/"),
        query=urlencode(query_items),
        fragment="",
    )
    return urlunsplit(cleaned)


def fingerprint_for_job(job: Job) -> str:
    title = normalize_text(job.title)
    company = normalize_text(job.company)
    location = normalize_text(job.location)

    combined = f"{title} | {company} | {location}".lower()
    combined = unicodedata.normalize("NFKD", combined)
    combined = combined.encode("ascii", "ignore").decode("ascii")
    combined = re.sub(r"[^a-z0-9]+", " ", combined)
    return normalize_text(combined)


class SQLiteJobRepository:
    """SQLite-backed repository for storing and looking up jobs."""

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        country TEXT,
        source TEXT,
        source_job_id TEXT,
        url TEXT,
        canonical_url TEXT,
        description TEXT,
        posted_date TEXT,
        discovered_at TEXT NOT NULL,
        first_seen_at TEXT NOT NULL,
        last_seen_at TEXT NOT NULL,
        notified_at TEXT,
        match_score REAL DEFAULT 0.0,
        match_reasons TEXT,
        status TEXT NOT NULL DEFAULT 'new',
        fingerprint TEXT
    )
    """

    INDEX_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_source_source_job_id ON jobs(source, source_job_id)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_discovered_at ON jobs(discovered_at)",
        "CREATE INDEX IF NOT EXISTS idx_jobs_notified_at ON jobs(notified_at)",
    ]

    def __init__(self, db_path: str | Path | None = None):
        target = Path(db_path) if db_path else Path(settings.database_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(target)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def initialize_database(self) -> None:
        with self._connect() as conn:
            conn.execute(self.CREATE_TABLE_SQL)
            for statement in self.INDEX_SQL:
                conn.execute(statement)

    def _job_from_row(self, row: sqlite3.Row | None) -> Job | None:
        if row is None:
            return None
        return Job(
            id=row["id"],
            title=row["title"],
            company=row["company"],
            location=row["location"],
            country=row["country"],
            source=row["source"],
            source_job_id=row["source_job_id"],
            url=row["url"],
            canonical_url=row["canonical_url"],
            description=row["description"],
            posted_date=row["posted_date"],
            discovered_at=row["discovered_at"],
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            notified_at=row["notified_at"],
            match_score=row["match_score"],
            match_reasons=(row["match_reasons"].split(";") if row["match_reasons"] else []),
            status=row["status"],
            fingerprint=row["fingerprint"],
        )

    def _row_from_job(self, job: Job) -> dict[str, Any]:
        if job.url:
            job.url = canonicalize_url(job.url)
        if job.canonical_url is None:
            job.canonical_url = canonicalize_url(job.url)
        if job.fingerprint is None:
            job.fingerprint = fingerprint_for_job(job)
        if job.discovered_at is None:
            job.discovered_at = datetime.now(timezone.utc)
        if job.first_seen_at is None:
            job.first_seen_at = job.discovered_at
        if job.last_seen_at is None:
            job.last_seen_at = job.discovered_at

        return {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "country": job.country,
            "source": job.source,
            "source_job_id": job.source_job_id,
            "url": job.url,
            "canonical_url": job.canonical_url,
            "description": job.description,
            "posted_date": job.posted_date.isoformat() if hasattr(job.posted_date, "isoformat") else job.posted_date,
            "discovered_at": job.discovered_at.isoformat() if hasattr(job.discovered_at, "isoformat") else job.discovered_at,
            "first_seen_at": job.first_seen_at.isoformat() if hasattr(job.first_seen_at, "isoformat") else job.first_seen_at,
            "last_seen_at": job.last_seen_at.isoformat() if hasattr(job.last_seen_at, "isoformat") else job.last_seen_at,
            "notified_at": job.notified_at.isoformat() if hasattr(job.notified_at, "isoformat") else job.notified_at,
            "match_score": job.match_score,
            "match_reasons": ";".join(job.match_reasons),
            "status": job.status,
            "fingerprint": job.fingerprint,
        }

    def insert_job(self, job: Job) -> Job:
        existing = self.find_duplicate_job(job)
        if existing is not None:
            return self.upsert_job(job)

        values = self._row_from_job(job)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO jobs (
                    title, company, location, country, source, source_job_id, url,
                    canonical_url, description, posted_date, discovered_at, first_seen_at,
                    last_seen_at, notified_at, match_score, match_reasons, status, fingerprint
                ) VALUES (
                    :title, :company, :location, :country, :source, :source_job_id, :url,
                    :canonical_url, :description, :posted_date, :discovered_at, :first_seen_at,
                    :last_seen_at, :notified_at, :match_score, :match_reasons, :status, :fingerprint
                )
                """,
                values,
            )
            job.id = cursor.lastrowid
            job.discovered_at = datetime.fromisoformat(values["discovered_at"]) if isinstance(values["discovered_at"], str) else job.discovered_at
            job.first_seen_at = datetime.fromisoformat(values["first_seen_at"]) if isinstance(values["first_seen_at"], str) else job.first_seen_at
            job.last_seen_at = datetime.fromisoformat(values["last_seen_at"]) if isinstance(values["last_seen_at"], str) else job.last_seen_at
        return job

    def update_job(self, job: Job) -> Job:
        if job.id is None:
            raise ValueError("Job id is required to update an existing row.")

        with self._connect() as conn:
            existing = self.get_job_by_id(job.id)
            if existing is None:
                raise ValueError(f"No job found with id {job.id}")

            if job.first_seen_at is None:
                job.first_seen_at = existing.first_seen_at
            if job.notified_at is None:
                job.notified_at = existing.notified_at
            if job.last_seen_at is None:
                job.last_seen_at = existing.last_seen_at

            values = self._row_from_job(job)
            conn.execute(
                """
                UPDATE jobs
                SET title = :title,
                    company = :company,
                    location = :location,
                    country = :country,
                    source = :source,
                    source_job_id = :source_job_id,
                    url = :url,
                    canonical_url = :canonical_url,
                    description = :description,
                    posted_date = :posted_date,
                    discovered_at = :discovered_at,
                    first_seen_at = :first_seen_at,
                    last_seen_at = :last_seen_at,
                    notified_at = :notified_at,
                    match_score = :match_score,
                    match_reasons = :match_reasons,
                    status = :status,
                    fingerprint = :fingerprint
                WHERE id = :id
                """,
                {**values, "id": job.id},
            )
            updated_row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job.id,)).fetchone()
            return self._job_from_row(updated_row)

    def upsert_job(self, job: Job) -> Job:
        existing = self.find_duplicate_job(job)
        if existing is None:
            return self.insert_job(job)

        if existing.first_seen_at is None and job.first_seen_at is not None:
            existing.first_seen_at = job.first_seen_at
        if existing.notified_at is None and job.notified_at is not None:
            existing.notified_at = job.notified_at

        if job.title:
            existing.title = job.title
        if job.company:
            existing.company = job.company
        if job.location:
            existing.location = job.location
        if job.country:
            existing.country = job.country
        if job.source:
            existing.source = job.source
        if job.source_job_id:
            existing.source_job_id = job.source_job_id
        if job.url:
            existing.url = job.url
        if job.canonical_url:
            existing.canonical_url = job.canonical_url
        if job.description:
            existing.description = job.description
        if job.posted_date is not None:
            existing.posted_date = job.posted_date
        if job.match_score is not None:
            existing.match_score = job.match_score
        if job.match_reasons:
            existing.match_reasons = job.match_reasons
        if job.status:
            existing.status = job.status
        if job.fingerprint:
            existing.fingerprint = job.fingerprint
        if job.last_seen_at is not None:
            existing.last_seen_at = job.last_seen_at
        else:
            existing.last_seen_at = datetime.now(timezone.utc)

        return self.update_job(existing)

    def get_job_by_id(self, job_id: int) -> Job | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return self._job_from_row(row)

    def get_job_by_url(self, url: str | None) -> Job | None:
        if not url:
            return None
        canonical = canonicalize_url(url)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE canonical_url = ? OR url = ? ORDER BY id DESC LIMIT 1",
                (canonical, url),
            ).fetchone()
            return self._job_from_row(row)

    def get_job_by_source_and_job_id(self, source: str | None, source_job_id: str | None) -> Job | None:
        if not source or not source_job_id:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE source = ? AND source_job_id = ? LIMIT 1",
                (source, source_job_id),
            ).fetchone()
            return self._job_from_row(row)

    def _lookup_by_fingerprint(self, fingerprint: str) -> Job | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE fingerprint = ? LIMIT 1",
                (fingerprint,),
            ).fetchone()
            return self._job_from_row(row)

    def find_duplicate_job(self, job: Job) -> Job | None:
        if job.source and job.source_job_id:
            match = self.get_job_by_source_and_job_id(job.source, job.source_job_id)
            if match is not None:
                return match

        canonical = canonicalize_url(job.url)
        if canonical:
            match = self.get_job_by_url(canonical)
            if match is not None:
                return match

        fingerprint = fingerprint_for_job(job)
        if fingerprint:
            match = self._lookup_by_fingerprint(fingerprint)
            if match is not None:
                return match

        return None

    def was_job_seen(self, job: Job | int) -> bool:
        if isinstance(job, int):
            return self.get_job_by_id(job) is not None
        return self.find_duplicate_job(job) is not None

    def was_job_notified(self, job_id: int) -> bool:
        job = self.get_job_by_id(job_id)
        return bool(job and job.notified_at is not None)

    def mark_job_notified(self, job_id: int, notified_at: datetime | str | None = None) -> Job | None:
        job = self.get_job_by_id(job_id)
        if job is None:
            return None
        value = notified_at or datetime.now(timezone.utc)
        job.notified_at = value
        job.status = "notified"
        with self._connect() as conn:
            conn.execute(
                "UPDATE jobs SET notified_at = ?, status = ? WHERE id = ?",
                (job.notified_at.isoformat() if hasattr(job.notified_at, "isoformat") else job.notified_at, job.status, job_id),
            )
        return self.get_job_by_id(job_id)

    def get_jobs_within_date_window(self, days: int = 14) -> list[Job]:
        from job_mentor.utils.dates import is_within_search_window

        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs").fetchall()
        jobs = [self._job_from_row(row) for row in rows]
        return [job for job in jobs if job is not None and is_within_search_window(job.posted_date, days=days)]

    def get_unnotified_jobs(self) -> list[Job]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs WHERE notified_at IS NULL ORDER BY discovered_at DESC").fetchall()
        return [job for job in (self._job_from_row(row) for row in rows) if job is not None]

    def get_newly_discovered_jobs(self, days: int = 14) -> list[Job]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE discovered_at >= ? ORDER BY discovered_at DESC",
                (cutoff,),
            ).fetchall()
        return [job for job in (self._job_from_row(row) for row in rows) if job is not None]
