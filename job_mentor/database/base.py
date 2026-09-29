class DatabaseClient:
    """Placeholder database client for job records and monitoring history."""

    def __init__(self, connection_string: str | None = None):
        self.connection_string = connection_string

    def connect(self):
        return {"status": "not_implemented", "message": "Database backend to be configured in a later stage."}

    def save_jobs(self, jobs):
        return {"saved": len(jobs) if jobs else 0, "status": "not_implemented"}

    def save_monitoring_run(self, payload):
        return {"status": "not_implemented", "payload": payload}
