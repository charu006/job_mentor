from __future__ import annotations

from job_mentor.collectors.duunitori import DuunitoriCollector
from job_mentor.collectors.monster_fi import MonsterFiCollector
from job_mentor.collectors.tyomarkkinatori import TyomarkkinatoriCollector
from job_mentor.config.settings import load_settings


def test_tyomarkkinatori_adapter_is_disabled_by_default():
    collector = TyomarkkinatoriCollector()
    assert collector.source_name == "tyomarkkinatori.fi"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_duunitori_adapter_is_disabled_by_default():
    collector = DuunitoriCollector()
    assert collector.source_name == "duunitori.fi"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_monster_fi_adapter_is_disabled_by_default():
    collector = MonsterFiCollector()
    assert collector.source_name == "monster.fi"
    assert collector.enabled is False
    assert collector.search_jobs() == []
    assert collector.get_status()["status"] == "disabled"


def test_stage5g_settings_expose_finland_flags():
    settings = load_settings()
    assert hasattr(settings, "tyomarkkinatori_enabled")
    assert hasattr(settings, "duunitori_enabled")
    assert hasattr(settings, "monster_fi_enabled")
    assert settings.tyomarkkinatori_enabled is False
    assert settings.duunitori_enabled is False
    assert settings.monster_fi_enabled is False


def test_finland_collectors_fail_gracefully_when_disabled():
    collectors = [
        TyomarkkinatoriCollector(),
        DuunitoriCollector(),
        MonsterFiCollector(),
    ]
    results = [collector.search_jobs() for collector in collectors]
    assert all(result == [] for result in results)
