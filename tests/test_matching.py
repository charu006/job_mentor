from datetime import datetime, timedelta, timezone

from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.matching.engine import MatchingEngine
from job_mentor.models.job import Job


def test_core_keywords_score_high_for_elastomer_titles():
    engine = MatchingEngine()
    job = Job(
        title="Elastomer Development Engineer",
        company="RubberTech GmbH",
        location="Berlin",
        source="jobs.arbeitsagentur.de",
        source_job_id="M-1",
        url="https://example.com/m-1",
        description="Develop elastomer formulations and compounds for automotive seals and polymer systems.",
        posted_date=(datetime.now(timezone.utc) - timedelta(days=3)).date().isoformat(),
    )
    result = engine.score_job(job)
    assert result.score >= 80
    assert result.category == "STRONG_MATCH"
    assert any("Elastomer" in reason or "elastomer" in reason for reason in result.reasons)


def test_polymer_science_title_is_strong_match():
    engine = MatchingEngine()
    job = Job(
        title="Polymer Scientist",
        description="Research polymer structures, formulations, and material behavior.",
    )
    result = engine.score_job(job)
    assert result.score >= 80
    assert result.category == "STRONG_MATCH"


def test_materials_development_title_is_strong_match():
    engine = MatchingEngine()
    job = Job(
        title="Materials Development Engineer - Polymer",
        description="Develop material systems and advanced polymer formulations.",
    )
    result = engine.score_job(job)
    assert result.score >= 80
    assert result.category == "STRONG_MATCH"


def test_rubber_technology_title_is_strong_match():
    engine = MatchingEngine()
    job = Job(
        title="Rubber Technology Engineer",
        description="Lead rubber formulation and compounding programs.",
    )
    result = engine.score_job(job)
    assert result.score >= 80
    assert result.category == "STRONG_MATCH"


def test_compound_development_engineer_is_strong_match():
    engine = MatchingEngine()
    job = Job(
        title="Compound Development Engineer",
        description="Develop rubber and polymer compounds for elastomer systems.",
    )
    result = engine.score_job(job)
    assert result.score >= 80
    assert result.category == "STRONG_MATCH"


def test_technical_material_abbreviations_contribute_without_being_overconfident():
    engine = MatchingEngine()
    job = Job(
        title="Materials Engineer",
        description="Work with EPDM, NBR, TPE and TPU compounds in development projects.",
    )
    result = engine.score_job(job)
    assert 40 <= result.score < 80
    assert result.category in {"POSSIBLE_MATCH", "GOOD_MATCH"}


def test_german_terms_are_detected():
    engine = MatchingEngine()
    job = Job(
        title="Werkstoffentwicklung / Kunststofftechnik",
        description="Entwicklung von Polymer- und Elastomerformulierungen in Deutschland.",
    )
    result = engine.score_job(job)
    assert result.score >= 70
    assert result.category in {"GOOD_MATCH", "STRONG_MATCH"}


def test_software_engineer_at_polymer_company_is_not_strong():
    engine = MatchingEngine()
    job = Job(
        title="Software Engineer",
        description="Works with a polymer company and supports internal tooling for product teams.",
    )
    result = engine.score_job(job)
    assert result.score < 40 or result.category == "IRRELEVANT"


def test_accountant_in_rubber_company_not_relevant():
    engine = MatchingEngine()
    job = Job(
        title="Accountant",
        description="Supports finance for a rubber manufacturer with multiple product lines.",
    )
    result = engine.score_job(job)
    assert result.score < 40
    assert result.category == "IRRELEVANT"


def test_generic_materials_engineer_needs_context():
    engine = MatchingEngine()
    job = Job(
        title="Materials Engineer",
        description="General materials support and process coordination.",
    )
    result = engine.score_job(job)
    assert result.score < 80
    assert result.category in {"POSSIBLE_MATCH", "IRRELEVANT"}


def test_title_match_weighs_more_than_description_only_incidentals():
    engine = MatchingEngine()
    title_job = Job(
        title="Elastomer Development Engineer",
        description="Support internal operations in a broad manufacturing environment.",
    )
    description_only = Job(
        title="Mechanical Engineer",
        description="Develops polymer seals, elastomer parts and materials for manufacturing lines.",
    )
    title_result = engine.score_job(title_job)
    desc_result = engine.score_job(description_only)
    assert title_result.score > desc_result.score


def test_reasons_are_generated_for_matches():
    engine = MatchingEngine()
    job = Job(title="Polymer R&D Engineer")
    result = engine.score_job(job)
    assert len(result.reasons) > 0
    assert result.score > 0


def test_scores_are_bounded_between_zero_and_one_hundred():
    engine = MatchingEngine()
    for title in ["Elastomer Engineer", "Polymer Scientist", "Software Engineer"]:
        job = Job(title=title)
        result = engine.score_job(job)
        assert 0 <= result.score <= 100


def test_empty_title_or_description_handled_safely():
    engine = MatchingEngine()
    empty_job = Job(title="", description="")
    result = engine.score_job(empty_job)
    assert result.score == 0
    assert result.category == "IRRELEVANT"


def test_unicode_and_punctuation_are_normalized():
    engine = MatchingEngine()
    job = Job(title="Kunststofftechnik / Werkstoffentwicklung!!!")
    result = engine.score_job(job)
    assert result.score >= 40


def test_matcher_can_filter_report_jobs_by_minimum_score():
    engine = MatchingEngine()
    strong = Job(title="Polymer Scientist", match_score=90, status="STRONG_MATCH")
    weak = Job(title="General Engineering", match_score=25, status="IRRELEVANT")
    filtered = engine.filter_report_jobs([strong, weak], minimum_score=40)
    assert filtered == [strong]


def test_matching_engine_integrates_with_database_and_report_pipeline(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    engine = MatchingEngine()

    job = Job(
        title="Elastomer Development Engineer",
        company="RubberTech GmbH",
        location="Düsseldorf",
        country="Germany",
        source="jobs.arbeitsagentur.de",
        source_job_id="match-01",
        url="https://example.com/jobs/match-01",
        description="Design elastomer compounds and polymer formulations for product development.",
        posted_date=(datetime.now(timezone.utc) - timedelta(days=2)).date().isoformat(),
    )

    result = engine.score_job(job)
    assert result.category in {"GOOD_MATCH", "STRONG_MATCH"}
    job.match_score = result.score
    job.match_reasons = result.reasons
    job.status = result.category

    repo.insert_job(job)
    stored = repo.get_job_by_source_and_job_id("jobs.arbeitsagentur.de", "match-01")
    assert stored is not None
    assert stored.match_score >= 40
    assert stored.status in {"GOOD_MATCH", "STRONG_MATCH"}
    assert len(stored.match_reasons) > 0
