from __future__ import annotations

import inspect
import urllib.request

from job_mentor.collectors import (
    BaseCollector,
    NoFluffJobsCollector,
    PracujCollector,
    RocketJobsCollector,
)
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.config.settings import load_settings


def test_stage5j_collectors_are_importable():
    assert PracujCollector.source_name == "pracuj.pl"
    assert NoFluffJobsCollector.source_name == "nofluffjobs.com"
    assert RocketJobsCollector.source_name == "rocketjobs.pl"


def test_stage5j_collectors_default_to_disabled():
    collectors = [PracujCollector(), NoFluffJobsCollector(), RocketJobsCollector()]
    for collector in collectors:
        assert collector.enabled is False
        assert collector.search_jobs() == []
        assert collector.get_status()["status"] == "disabled"


def test_stage5j_disabled_collectors_make_zero_network_calls(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise AssertionError("unexpected network request")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    for collector in [PracujCollector(), NoFluffJobsCollector(), RocketJobsCollector()]:
        assert collector.search_jobs() == []


def test_stage5j_settings_flags_loaded():
    settings = load_settings()
    assert hasattr(settings, "pracuj_enabled")
    assert hasattr(settings, "nofluffjobs_enabled")
    assert hasattr(settings, "rocketjobs_enabled")
    assert settings.pracuj_enabled is False
    assert settings.nofluffjobs_enabled is False
    assert settings.rocketjobs_enabled is False


def test_stage5j_collectors_respect_basecollector_interface():
    collectors = [PracujCollector(), NoFluffJobsCollector(), RocketJobsCollector()]
    for collector in collectors:
        assert isinstance(collector, BaseCollector)
        assert hasattr(collector, "search_jobs")
        assert hasattr(collector, "normalize_raw_job")
        assert hasattr(collector, "get_status")


def test_stage5j_no_html_scraping_or_undocumented_api_usage():
    for collector in [PracujCollector(), NoFluffJobsCollector(), RocketJobsCollector()]:
        source = inspect.getsource(type(collector))
        lowered = source.lower()
        assert "beautifulsoup" not in lowered
        assert "html.parser" not in lowered
        assert "requests.get" not in lowered
        assert "urlopen" not in lowered


def test_stage5j_error_handling_is_safe():
    for collector in [PracujCollector(enabled=True), NoFluffJobsCollector(enabled=True), RocketJobsCollector(enabled=True)]:
        assert collector.search_jobs() == []
        assert collector.get_status()["status"] == "enabled"


def test_stage5j_search_terms_remain_intact():
    required = {
        "elastomer",
        "polymer",
        "polymer science",
        "polymer technology",
        "rubber technology",
        "material development",
        "product development",
        "elastomer expert",
    }
    assert required.issubset(set(DEFAULT_SEARCH_TERMS))


def test_stage5j_readme_documents_portal_status_and_reasons():
    import pathlib

    readme_text = pathlib.Path("README.md").read_text(encoding="utf-8")
    assert "Stage 5J Poland portal status" in readme_text
    assert "pracuj.pl" in readme_text.lower()
    assert "nofluffjobs.com" in readme_text.lower()
    assert "rocketjobs.pl" in readme_text.lower()


def test_stage5j_no_real_network_calls_during_tests(monkeypatch):
    def fail_network(*args, **kwargs):
        raise AssertionError("real network access attempted")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)

    for collector in [PracujCollector(), NoFluffJobsCollector(), RocketJobsCollector()]:
        assert collector.search_jobs() == []
