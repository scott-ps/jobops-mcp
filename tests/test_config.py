import os
import subprocess
import sys

import config
import db

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_data_dir_defaults_to_project_folder(monkeypatch):
    monkeypatch.delenv("JOBOPS_DATA_DIR", raising=False)
    assert config.data_dir() == config.BASE_DIR


def test_data_dir_uses_env_var(monkeypatch, tmp_path):
    monkeypatch.setenv("JOBOPS_DATA_DIR", str(tmp_path))
    assert config.data_dir() == str(tmp_path)


def test_init_db_creates_missing_data_folder(monkeypatch, tmp_path):
    db_path = tmp_path / "not_yet_created" / "jobops.db"
    monkeypatch.setattr(db, "DB_PATH", str(db_path))
    db.init_db()
    assert db_path.exists()


def test_importing_server_creates_no_files(tmp_path):
    """Importing server.py must not create the database; only starting it should."""
    env = {**os.environ, "JOBOPS_DATA_DIR": str(tmp_path)}
    subprocess.run([sys.executable, "-c", "import server"], cwd=PROJECT_ROOT, env=env, check=True)
    assert list(tmp_path.iterdir()) == []