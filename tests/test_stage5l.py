from __future__ import annotations

import inspect
import urllib.request

from job_mentor.collectors import BaseCollector, EuraxessCollector, EuresCollector, JobsIrelandEuCollector
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.config.settings import load_settings


def test_stage5l_collectors_import_correctly():
    assert EuresCollector.source_name == "eures.europa.eu"
    assert EuraxessCollector.source_name == "euraxess.ec.europa.eu"
    assert JobsIrelandEuCollector.source_name == "jobsireland.eu"


def test_stage5l_default_configuration_is_disabled():
    collectors = [EuresCollector(), EuraxessCollector(), JobsIrelandEuCollector()]
    for collector in collectors:
        assert collector.enabled is False
        assert collector.search_jobs() == []
        assert collector.get_status()["status"] == "disabled"


def test_stage5l_disabled_collectors_make_zero_network_calls(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise AssertionError("unexpected network request")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    for collector in [EuresCollector(), EuraxessCollector(), JobsIrelandEuCollector()]:
        assert collector.search_jobs() == []


def test_stage5l_settings_flags_load_correctly():
    settings = load_settings()
    assert hasattr(settings, "eures_enabled")
    assert hasattr(settings, "euraxess_enabled")
    assert hasattr(settings, "jobsireland_eu_enabled")
    assert settings.eures_enabled is False
    assert settings.euraxess_enabled is False
    assert settings.jobsireland_eu_enabled is False


def test_stage5l_collectors_respect_basecollector_interface():
    collectors = [EuresCollector(), EuraxessCollector(), JobsIrelandEuCollector()]
    for collector in collectors:
        assert isinstance(collector, BaseCollector)
        assert hasattr(collector, "search_jobs")
        assert hasattr(collector, "normalize_raw_job")
        assert hasattr(collector, "get_status")


def test_stage5l_no_html_scraping_or_undocumented_api_usage():
    for collector in [EuresCollector(), EuraxessCollector(), JobsIrelandEuCollector()]:
        source = inspect.getsource(type(collector)).lower()
        assert "beautifulsoup" not in source
        assert "html.parser" not in source
        assert "requests.get" not in source
        assert "urlopen" not in source
        assert "scrape" not in source
        assert "undocumented" not in source.lower()


def test_stage5l_error_handling_is_safe():
    for collector in [EuresCollector(enabled=True), EuraxessCollector(enabled=True), JobsIrelandEuCollector(enabled=True)]:
        assert collector.search_jobs() == []
        assert collector.get_status()["status"] == "enabled"


def test_stage5l_search_vocabulary_remains_intact():
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


def test_stage5l_new_terms_are_additive():
    for term in [
        "polymer chemistry",
        "materials science",
        "materials engineering",
        "research scientist",
        "research engineer",
    ]:
        assert term in DEFAULT_SEARCH_TERMS


def test_stage5l_current_domain_redirect_handling_and_euraxess_legacy_warning():
    collector = EuraxessCollector(base_url="https://euraxess.eu")
    assert collector.base_url == "https://euraxess.ec.europa.eu"
    status = collector.get_status()
    assert "legacy" in status["reason"].lower() or "official current domain" in status["reason"].lower()

    status2 = JobsIrelandEuCollector(base_url="https://jobsireland.ie").get_status()
    assert "not the same" in status2["reason"].lower() or "separate domain" in status2["reason"].lower()


def test_stage5l_readme_documents_the_stage_and_trello_warning():
    import pathlib

    readme_text = pathlib.Path("README.md").read_text(encoding="utf-8")
    assert "Stage 5L EU-wide / Euraxess portal status" in readme_text
    assert "EURES" in readme_text
    assert "EURAXESS" in readme_text
    assert "jobsireland.eu" in readme_text.lower()
    assert "Trello is not treated as a generic job portal" in readme_text


def test_stage5l_no_real_external_network_calls_during_tests(monkeypatch):
    def fail_network(*args, **kwargs):
        raise AssertionError("real network access attempted")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)

    for collector in [EuresCollector(), EuraxessCollector(), JobsIrelandEuCollector()]:
        assert collector.search_jobs() == []
