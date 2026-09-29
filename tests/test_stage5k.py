from __future__ import annotations

import inspect
import urllib.request

from job_mentor.collectors import (
    AdemCollector,
    BaseCollector,
    JobsLuCollector,
    MoovijobCollector,
)
from job_mentor.config.search_terms import DEFAULT_SEARCH_TERMS
from job_mentor.config.settings import load_settings


def test_stage5k_collectors_import_correctly():
    assert AdemCollector.source_name == "adem.public.lu"
    assert JobsLuCollector.source_name == "jobs.lu"
    assert MoovijobCollector.source_name == "moovijob.com"


def test_stage5k_collectors_default_to_disabled():
    collectors = [AdemCollector(), JobsLuCollector(), MoovijobCollector()]
    for collector in collectors:
        assert collector.enabled is False
        assert collector.search_jobs() == []
        assert collector.get_status()["status"] == "disabled"


def test_stage5k_disabled_collectors_make_zero_network_calls(monkeypatch):
    def fail_urlopen(*args, **kwargs):
        raise AssertionError("unexpected network request")

    monkeypatch.setattr(urllib.request, "urlopen", fail_urlopen)

    for collector in [AdemCollector(), JobsLuCollector(), MoovijobCollector()]:
        assert collector.search_jobs() == []


def test_stage5k_settings_flags_load_correctly():
    settings = load_settings()
    assert hasattr(settings, "adem_enabled")
    assert hasattr(settings, "jobs_lu_enabled")
    assert hasattr(settings, "moovijob_enabled")
    assert settings.adem_enabled is False
    assert settings.jobs_lu_enabled is False
    assert settings.moovijob_enabled is False


def test_stage5k_collectors_respect_basecollector_interface():
    collectors = [AdemCollector(), JobsLuCollector(), MoovijobCollector()]
    for collector in collectors:
        assert isinstance(collector, BaseCollector)
        assert hasattr(collector, "search_jobs")
        assert hasattr(collector, "normalize_raw_job")
        assert hasattr(collector, "get_status")


def test_stage5k_no_html_scraping_or_undocumented_api_usage():
    for collector in [AdemCollector(), JobsLuCollector(), MoovijobCollector()]:
        source = inspect.getsource(type(collector)).lower()
        assert "beautifulsoup" not in source
        assert "html.parser" not in source
        assert "requests.get" not in source
        assert "urllib.request" not in source
        assert "urlopen" not in source
        assert "lxml" not in source


def test_stage5k_error_handling_is_safe():
    for collector in [AdemCollector(enabled=True), JobsLuCollector(enabled=True), MoovijobCollector(enabled=True)]:
        assert collector.search_jobs() == []
        assert collector.get_status()["status"] == "enabled"


def test_stage5k_search_vocabulary_remains_intact():
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


def test_stage5k_luxembourg_terms_are_additive():
    for term in [
        "élastomère",
        "polymère",
        "science des polymères",
        "technologie des polymères",
        "caoutchouc",
        "technologie du caoutchouc",
        "développement des matériaux",
        "développement produit",
        "ingénieur matériaux",
    ]:
        assert term in DEFAULT_SEARCH_TERMS


def test_stage5k_readme_documents_portal_status_and_reason():
    import pathlib

    readme_text = pathlib.Path("README.md").read_text(encoding="utf-8")
    assert "Stage 5K Luxembourg portal status" in readme_text
    assert "adem.public.lu" in readme_text.lower()
    assert "jobs.lu" in readme_text.lower()
    assert "moovijob.com" in readme_text.lower()


def test_stage5k_no_real_external_network_calls_during_tests(monkeypatch):
    def fail_network(*args, **kwargs):
        raise AssertionError("real network access attempted")

    monkeypatch.setattr(urllib.request, "urlopen", fail_network)

    for collector in [AdemCollector(), JobsLuCollector(), MoovijobCollector()]:
        assert collector.search_jobs() == []
