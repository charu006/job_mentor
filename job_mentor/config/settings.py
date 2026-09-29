from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    log_level: str = "INFO"
    search_window_days: int = 14
    recipient_email: str | None = None
    monitoring_enabled: bool = False
    job_portals: tuple[str, ...] = (
        "Arbeitsagentur",
        "StepStone",
        "Meinestadt",
        "WerkNL",
        "NationaleVacaturebank",
        "JobDigger",
        "ArbeitSwiss",
        "JobsCH",
        "JobUpCH",
        "JobNet",
        "Ofir",
        "WorkInDenmark",
        "PublicJobs",
        "IrishJobs",
        "RecruitIreland",
        "Iefp",
        "NetEmpregos",
        "Beebez",
        "Tyomarkkinatori",
        "Duunitori",
        "MonsterFi",
        "Arbetsformedlingen",
        "AcademicWork",
        "JobbSafari",
    )
    arbeitsagentur_enabled: bool = True
    stepstone_enabled: bool = False
    meinestadt_enabled: bool = False
    werk_nl_enabled: bool = False
    nationalevacaturebank_enabled: bool = False
    jobdigger_enabled: bool = False
    jobdigger_api_key: str | None = None
    arbeit_swiss_enabled: bool = False
    jobs_ch_enabled: bool = False
    jobup_ch_enabled: bool = False
    jobnet_enabled: bool = False
    ofir_enabled: bool = False
    workindenmark_enabled: bool = False
    publicjobs_enabled: bool = False
    irishjobs_enabled: bool = False
    recruitireland_enabled: bool = False
    iefp_enabled: bool = False
    net_empregos_enabled: bool = False
    beebez_enabled: bool = False
    tyomarkkinatori_enabled: bool = False
    duunitori_enabled: bool = False
    monster_fi_enabled: bool = False
    arbetsformedlingen_enabled: bool = True
    academicwork_enabled: bool = False
    jobbsafari_enabled: bool = False
    database_path: str = "data/job_mentor.db"
    timezone: str = "Europe/Berlin"
    report_hour: int = 12
    report_minute: int = 0


def load_settings() -> AppSettings:
    def _as_bool(value: str | None, default: bool) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    return AppSettings(
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        search_window_days=int(os.getenv("SEARCH_WINDOW_DAYS", "14")),
        recipient_email=os.getenv("RECIPIENT_EMAIL"),
        monitoring_enabled=os.getenv("MONITORING_ENABLED", "false").lower() == "true",
        job_portals=tuple(
            portal.strip()
            for portal in os.getenv(
                "JOB_PORTALS",
                "Arbeitsagentur,StepStone,Meinestadt,WerkNL,NationaleVacaturebank,JobDigger,ArbeitSwiss,JobsCH,JobUpCH,JobNet,Ofir,WorkInDenmark,PublicJobs,IrishJobs,RecruitIreland,Iefp,NetEmpregos,Beebez,Tyomarkkinatori,Duunitori,MonsterFi,Arbetsformedlingen,AcademicWork,JobbSafari",
            ).split(",")
            if portal.strip()
        ),
        arbeitsagentur_enabled=_as_bool(os.getenv("ARBEITSAGENTUR_ENABLED"), True),
        stepstone_enabled=_as_bool(os.getenv("STEPSTONE_ENABLED"), False),
        meinestadt_enabled=_as_bool(os.getenv("MEINESTADT_ENABLED"), False),
        werk_nl_enabled=_as_bool(os.getenv("WERK_NL_ENABLED"), False),
        nationalevacaturebank_enabled=_as_bool(os.getenv("NATIONALEVACATUREBANK_ENABLED"), False),
        jobdigger_enabled=_as_bool(os.getenv("JOBDIGGER_ENABLED"), False),
        jobdigger_api_key=os.getenv("JOBDIGGER_API_KEY") or None,
        arbeit_swiss_enabled=_as_bool(os.getenv("ARBEIT_SWISS_ENABLED"), False),
        jobs_ch_enabled=_as_bool(os.getenv("JOBS_CH_ENABLED"), False),
        jobup_ch_enabled=_as_bool(os.getenv("JOBUP_CH_ENABLED"), False),
        jobnet_enabled=_as_bool(os.getenv("JOBNET_ENABLED"), False),
        ofir_enabled=_as_bool(os.getenv("OFIR_ENABLED"), False),
        workindenmark_enabled=_as_bool(os.getenv("WORKINDENMARK_ENABLED"), False),
        publicjobs_enabled=_as_bool(os.getenv("PUBLICJOBS_ENABLED"), False),
        irishjobs_enabled=_as_bool(os.getenv("IRISHJOBS_ENABLED"), False),
        recruitireland_enabled=_as_bool(os.getenv("RECRUITIRELAND_ENABLED"), False),
        iefp_enabled=_as_bool(os.getenv("IEFP_ENABLED"), False),
        net_empregos_enabled=_as_bool(os.getenv("NET_EMPREGOS_ENABLED"), False),
        beebez_enabled=_as_bool(os.getenv("BEEBEZ_ENABLED"), False),
        tyomarkkinatori_enabled=_as_bool(os.getenv("TYOMARKKINATORI_ENABLED"), False),
        duunitori_enabled=_as_bool(os.getenv("DUUNITORI_ENABLED"), False),
        monster_fi_enabled=_as_bool(os.getenv("MONSTER_FI_ENABLED"), False),
        arbetsformedlingen_enabled=_as_bool(os.getenv("ARBETSFORMEDLINGEN_ENABLED"), True),
        academicwork_enabled=_as_bool(os.getenv("ACADEMICWORK_ENABLED"), False),
        jobbsafari_enabled=_as_bool(os.getenv("JOBBSAFARI_ENABLED"), False),
        database_path=os.getenv("DATABASE_PATH", "data/job_mentor.db"),
        timezone=os.getenv("TIMEZONE", "Europe/Berlin"),
        report_hour=int(os.getenv("REPORT_HOUR", "12")),
        report_minute=int(os.getenv("REPORT_MINUTE", "0")),
    )


settings = load_settings()
