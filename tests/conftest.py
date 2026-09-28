import pytest

import db


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Point db at a throwaway SQLite file so the real jobops.db is never touched.
    pytest deletes tmp_path afterwards, and monkeypatch restores DB_PATH."""
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test_jobops.db"))
    db.init_db()