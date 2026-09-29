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
    )


settings = load_settings()
