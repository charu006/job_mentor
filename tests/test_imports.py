from job_mentor.config.settings import AppSettings
from job_mentor.config.sites import DEFAULT_SITES
from job_mentor.config.keywords import ELASTOMER_KEYWORDS
from job_mentor.core.logging_config import configure_logging


def test_package_imports():
    assert AppSettings is not None
    assert DEFAULT_SITES is not None
    assert ELASTOMER_KEYWORDS is not None
    assert configure_logging is not None


def test_logging_configures_without_error():
    logger = configure_logging()
    assert logger.name == "job_mentor"
