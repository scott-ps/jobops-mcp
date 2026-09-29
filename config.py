"""Shared settings: where JobOps keeps its persistent data."""

import os

# The project folder (where this file lives)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def data_dir() -> str:
    """Folder for persistent data: the SQLite database and generated documents.

    Defaults to the project folder. Set JOBOPS_DATA_DIR to keep data somewhere
    else, e.g. a Docker volume mounted at /data.
    """
    # Using `or` instead of a .get() default means an empty JOBOPS_DATA_DIR
    # is treated the same as an unset one
    return os.path.abspath(os.environ.get("JOBOPS_DATA_DIR") or BASE_DIR)
