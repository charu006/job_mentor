from __future__ import annotations

from job_mentor.collectors.beebez import BeebezCollector
from job_mentor.collectors.iefp import IefpCollector
from job_mentor.collectors.net_empregos import NetEmpregosCollector
from job_mentor.config.settings import load_settings


def test_iefp_adapter_is_disabled_by_default():
    collector = IefpCollector()
    assert collector.source_name == "iefp.pt"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_beebez_adapter_is_disabled_by_default():
    collector = BeebezCollector()
    assert collector.source_name == "beebez.pt"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_stage5f_settings_expose_portugal_flags():
    settings = load_settings()
    assert hasattr(settings, "iefp_enabled")
    assert hasattr(settings, "net_empregos_enabled")
    assert hasattr(settings, "beebez_enabled")
    assert settings.iefp_enabled is False
    assert settings.net_empregos_enabled is False
    assert settings.beebez_enabled is False


def test_portugal_collectors_fail_gracefully_when_disabled():
    collectors = [
        IefpCollector(),
        BeebezCollector(),
    ]
    results = [collector.search_jobs() for collector in collectors]
    assert all(result == [] for result in results)


def test_net_empregos_rss_parser_handles_official_feed(monkeypatch):
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Net Empregos</title>
        <link>https://www.net-empregos.com</link>
        <item>
          <title>Polymer Engineer</title>
          <link>https://www.net-empregos.com/oferta/123</link>
          <description>Develop polymer and elastomer materials for industrial production.</description>
          <guid>123</guid>
          <pubDate>Tue, 25 Sep 2026 12:00:00 +0000</pubDate>
        </item>
      </channel>
    </rss>
    '''
    collector = NetEmpregosCollector(enabled=True)
    monkeypatch.setattr(collector, "_fetch_feed", lambda: xml)
    jobs = collector.search_jobs()
    assert len(jobs) == 1
    assert jobs[0].title == "Polymer Engineer"
    assert jobs[0].company is None
    assert jobs[0].source == "net-empregos.com"
    assert jobs[0].country == "Portugal"


def test_portugal_collectors_normalize_common_fields():
    raw_job = {
        "title": "Materials Scientist",
        "company": "Porto Polymer Lab",
        "location": "Porto",
        "description": "Work on polymer and elastomer development projects.",
        "url": "https://example.com/jobs/pt-9?ref=source",
        "id": "PT-9",
        "published_at": "2026-09-25T12:00:00Z",
    }
    for collector in [IefpCollector(), BeebezCollector(), NetEmpregosCollector(enabled=True)]:
        normalized = collector.normalize_raw_job(raw_job)
        assert normalized is not None
        assert normalized.title == "Materials Scientist"
        assert normalized.company == "Porto Polymer Lab"
        assert normalized.source == collector.source_name
        assert normalized.url == "https://example.com/jobs/pt-9"
        assert normalized.country == "Portugal"
