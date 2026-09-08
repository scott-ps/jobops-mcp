import pytest
import db

@pytest.fixture(autouse=True)
def isolated_db(tmp_path):
    """
    Redirect db.DB_PATH to a temporary directory for every test.
    pytest automatically discards tmp_path after each test, so the
    real jobops.db is never read or written during the test suite.
    """
    original_path = db.DB_PATH
    db.DB_PATH = str(tmp_path / "test_jobops.db")
    db.init_db()
    yield
    db.DB_PATH = original_path

def test_add_and_get_application():
    """Verify an application can be created and retrieved."""
    app_id = db.add_application("Test Corp", "Automation Engineer", "Test notes")
    assert app_id is not None

    apps = db.list_applications()
    assert len(apps) == 1
    assert apps[0]["company"] == "Test Corp"
    assert apps[0]["status"] == db.ApplicationStatus.APPLIED.value

def test_update_status():
    """Verify status transitions are persisted correctly."""
    app_id = db.add_application("Update Corp", "Tester")
    success = db.update_status(app_id, db.ApplicationStatus.INTERVIEWING)
    assert success is True

    apps = db.list_applications()
    assert apps[0]["status"] == db.ApplicationStatus.INTERVIEWING.value

def test_update_nonexistent_application():
    """Verify updating a non-existent ID fails gracefully."""
    success = db.update_status(9999, db.ApplicationStatus.REJECTED)
    assert success is False