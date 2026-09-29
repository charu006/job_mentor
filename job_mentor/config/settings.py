from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    log_level: str = "INFO"
    search_window_days: int = 14
    recipient_email: str | None = None
    monitoring_enabled: bool = False
    job_portals: tuple[str, ...] = ("EURES", "LinkedIn", "Indeed", "StepStone")
    database_path: str = "data/job_mentor.db"
    timezone: str = "Europe/Berlin"
    report_hour: int = 12
    report_minute: int = 0


def load_settings() -> AppSettings:
    return AppSettings(
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        search_window_days=int(os.getenv("SEARCH_WINDOW_DAYS", "14")),
        recipient_email=os.getenv("RECIPIENT_EMAIL"),
        monitoring_enabled=os.getenv("MONITORING_ENABLED", "false").lower() == "true",
        job_portals=tuple(
            portal.strip()
            for portal in os.getenv("JOB_PORTALS", "EURES,LinkedIn,Indeed,StepStone").split(",")
            if portal.strip()
        ),
        database_path=os.getenv("DATABASE_PATH", "data/job_mentor.db"),
        timezone=os.getenv("TIMEZONE", "Europe/Berlin"),
        report_hour=int(os.getenv("REPORT_HOUR", "12")),
        report_minute=int(os.getenv("REPORT_MINUTE", "0")),
    )


settings = load_settings()
