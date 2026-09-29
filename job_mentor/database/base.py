from __future__ import annotations

from job_mentor.database.repository import SQLiteJobRepository


class DatabaseClient:
    """Thin compatibility wrapper around the SQLite repository used by the app."""

    def __init__(self, connection_string: str | None = None):
        self.repository = SQLiteJobRepository(connection_string)

    def connect(self):
        self.repository.initialize_database()
        return self.repository

    def save_jobs(self, jobs):
        for job in jobs:
            self.repository.upsert_job(job)
        return {"saved": len(jobs) if jobs else 0, "status": "ok"}

    def save_monitoring_run(self, payload):
        return {"status": "not_implemented", "payload": payload}
