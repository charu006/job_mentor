from datetime import datetime, timedelta, timezone

from job_mentor.config.settings import AppSettings, load_settings
from job_mentor.database.repository import SQLiteJobRepository
from job_mentor.models.job import Job
from job_mentor.utils.dates import is_within_search_window


def make_job(**overrides):
    now = datetime.now(timezone.utc)
    payload = {
        "title": "Senior Elastomer Scientist",
        "company": "RubberTech Labs",
        "location": "Düsseldorf, Germany",
        "country": "Germany",
        "source": "EURES",
        "source_job_id": "JOB-1001",
        "url": "https://example.com/jobs/1001?utm_source=email",
        "description": "Develop elastomer compounds and advanced polymer systems.",
        "posted_date": (now - timedelta(days=2)).date().isoformat(),
        "discovered_at": now,
        "first_seen_at": now,
        "last_seen_at": now,
        "notified_at": None,
        "match_score": 0.92,
        "match_reasons": ["elastomer", "polymer"],
        "status": "new",
    }
    payload.update(overrides)
    return Job(**payload)


def test_database_initialization(tmp_path):
    db_path = tmp_path / "job_mentor.db"
    repo = SQLiteJobRepository(db_path=str(db_path))
    repo.initialize_database()
    assert db_path.exists()


def test_insert_and_retrieve_job(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    job = make_job()
    saved = repo.insert_job(job)
    assert saved.id is not None
    fetched = repo.get_job_by_id(saved.id)
    assert fetched is not None
    assert fetched.title == job.title


def test_update_job(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    job = make_job(title="Initial title")
    saved = repo.insert_job(job)
    saved.title = "Updated title"
    saved.location = "Berlin, Germany"
    updated = repo.update_job(saved)
    assert updated.title == "Updated title"
    assert updated.location == "Berlin, Germany"


def test_duplicate_url_is_detected(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    job = make_job(url="https://example.com/jobs/dup?utm_source=email")
    repo.insert_job(job)
    duplicate = make_job(url="https://example.com/jobs/dup", source_job_id="OTHER")
    existing = repo.find_duplicate_job(duplicate)
    assert existing is not None
    assert existing.url == "https://example.com/jobs/dup"


def test_duplicate_source_and_source_job_id_is_detected(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    job = make_job(source="EURES", source_job_id="UNIQUE-42")
    repo.insert_job(job)
    duplicate = make_job(source="EURES", source_job_id="UNIQUE-42", url="https://different.example")
    existing = repo.find_duplicate_job(duplicate)
    assert existing is not None
    assert existing.source_job_id == "UNIQUE-42"


def test_fallback_fingerprint_duplicate_is_detected(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    job = make_job(title="Senior Elastomer Scientist!", company="RubberTech Labs", location="Düsseldorf, Germany")
    repo.insert_job(job)
    duplicate = make_job(
        title="senior elastomer scientist",
        company="  RubberTech Labs  ",
        location="Dusseldorf Germany",
        source="LinkedIn",
        source_job_id="NEW-123",
        url="https://other.example/xyz",
    )
    existing = repo.find_duplicate_job(duplicate)
    assert existing is not None
    assert existing.company == "RubberTech Labs"


def test_different_jobs_are_not_merged(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    repo.insert_job(make_job(title="Senior Elastomer Scientist", source_job_id="A-1", url="https://example.com/a"))
    repo.insert_job(make_job(title="Senior Polymer Chemist", source_job_id="B-2", url="https://example.com/b"))
    assert repo.get_job_by_url("https://example.com/a") is not None
    assert repo.get_job_by_url("https://example.com/b") is not None


def test_search_window_includes_recent_jobs():
    recent_date = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    assert is_within_search_window(recent_date, days=14) is True


def test_search_window_handles_exact_boundary():
    boundary = (datetime.now(timezone.utc) - timedelta(days=14)).date().isoformat()
    assert is_within_search_window(boundary, days=14) is True


def test_search_window_excludes_old_jobs():
    old_date = (datetime.now(timezone.utc) - timedelta(days=15)).date().isoformat()
    assert is_within_search_window(old_date, days=14) is False


def test_search_window_handles_future_date_safely():
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()
    assert is_within_search_window(future_date, days=14) is False


def test_search_window_handles_missing_date():
    assert is_within_search_window(None, days=14) is False


def test_search_window_handles_invalid_date():
    assert is_within_search_window("not-a-date", days=14) is False


def test_search_window_handles_timezone_aware_datetime():
    aware = datetime.now(timezone.utc) - timedelta(days=5)
    assert is_within_search_window(aware, days=14) is True


def test_mark_job_notified_and_retrieve_unnotified(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    job = make_job(source_job_id="NOTIFY-1")
    repo.insert_job(job)
    repo.mark_job_notified(job.id)
    assert repo.was_job_notified(job.id) is True
    assert repo.get_unnotified_jobs() == []


def test_first_seen_at_and_notified_at_preserved_on_update(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    created = datetime.now(timezone.utc) - timedelta(days=30)
    job = make_job(first_seen_at=created, discovered_at=created, notified_at=created)
    saved = repo.insert_job(job)
    saved.title = "Updated Title"
    saved.last_seen_at = datetime.now(timezone.utc)
    updated = repo.update_job(saved)
    assert updated.first_seen_at == created
    assert updated.notified_at == created


def test_repository_loads_settings_database_path():
    settings = load_settings()
    assert settings.database_path.endswith("job_mentor.db")


def test_job_repository_upsert_updates_last_seen_but_preserves_first_seen(tmp_path):
    repo = SQLiteJobRepository(db_path=str(tmp_path / "job_mentor.db"))
    repo.initialize_database()
    initial = datetime.now(timezone.utc) - timedelta(days=4)
    job = make_job(first_seen_at=initial, discovered_at=initial, last_seen_at=initial)
    saved = repo.insert_job(job)
    later = datetime.now(timezone.utc)
    saved.last_seen_at = later
    saved.description = "Updated description"
    updated = repo.upsert_job(saved)
    assert updated.first_seen_at == initial
    assert updated.last_seen_at == later
    assert updated.description == "Updated description"
