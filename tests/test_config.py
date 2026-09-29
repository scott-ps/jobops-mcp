import os
import shutil
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
    """Importing server.py must not create any files (database, resume, ...); only starting it should."""
    # Some paths (like the resume) come from the modules' own location, so import a copy
    # of them from tmp_path. The real project and data folders are never touched.
    for name in os.listdir(PROJECT_ROOT):
        if name.endswith(".py"):
            shutil.copy(os.path.join(PROJECT_ROOT, name), tmp_path)
    (tmp_path / "profile_docs").mkdir()

    def files():
        return {p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*")}

    before = files()

    # Runs in a fresh Python process, since server may already be imported in this one.
    # No bytecode, so __pycache__ doesn't show up as a new file.
    env = {**os.environ, "JOBOPS_DATA_DIR": str(tmp_path / "data"), "PYTHONDONTWRITEBYTECODE": "1"}
    subprocess.run([sys.executable, "-c", "import server"], cwd=tmp_path, env=env, check=True)
    assert files() == before
