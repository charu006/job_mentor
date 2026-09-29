from job_mentor.core.logging_config import configure_logging
from job_mentor.config.settings import settings


def main() -> None:
    logger = configure_logging(log_level=settings.log_level)
    logger.info("Job Mentor started in Stage 1 scaffold mode.")
    logger.info(
        "Monitoring window: %s days | recipient configured: %s",
        settings.search_window_days,
        bool(settings.recipient_email),
    )


if __name__ == "__main__":
    main()
