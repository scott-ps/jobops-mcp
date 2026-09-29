"""SQLite persistence layer for the job application pipeline."""

from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import logging
import os
import sqlite3
from typing import List, Dict, Any, Optional

import config


# Set up logger for db
logger = logging.getLogger(__name__)

# The database lives in the data folder (see config.py). This is resolved once,
# at import time; tests point it at a temporary file instead (see tests/conftest.py).
DB_PATH = os.path.join(config.data_dir(), "jobops.db")


@contextmanager
def get_connection():
    """Yield a sqlite3 connection, guaranteeing it's closed even if an
    exception is raised while it's in use."""
    # DB_PATH is read on each call (not captured at import), which is what
    # lets tests swap in a different database file
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


# Define application status options to be used.
# Subclassing str means each member is also a plain string: sqlite3 can store it
# directly, and it compares equal to its value (ApplicationStatus.APPLIED == "Applied").
# FastMCP also lists these values in the tool schema, so clients see the valid options.
# Note: f-strings render a member as "ApplicationStatus.APPLIED", so use .value for display text.
class ApplicationStatus(str, Enum):
    APPLIED = "Applied"
    SCREENING = "Screen scheduled"
    INTERVIEWING = "Interviewing"
    OFFER = "Offer received"
    REJECTED = "Rejected"


def init_db():
    """Initialize the SQLite database with the applications table."""
    logger.info("Initializing SQLite database...")

    # Create the data folder first; otherwise SQLite fails with "unable to open database file"
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with get_connection() as conn:
        cursor = conn.cursor()

        # IF NOT EXISTS makes this safe to run on every server start.
        # Timestamps are stored as "YYYY-MM-DD HH:MM:SS" text (SQLite has no
        # native datetime type); this format also sorts correctly as a string.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied',
                date_applied TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                notes TEXT
            )
        """)
        conn.commit()
    logger.info(f"DB initialized")


def add_application(company: str, role: str, notes: str = "") -> int:
    """Insert a new application with status 'Applied' and return its ID."""
    # Local time. audit_stale_applications in server.py parses this same format back.
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()

        # "?" placeholders let sqlite3 insert the values safely (no SQL injection)
        cursor.execute("""
            INSERT INTO applications (company, role, status, date_applied, last_updated, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company, role, ApplicationStatus.APPLIED.value, now, now, notes))

        # The auto-generated ID of the row just inserted
        app_id = cursor.lastrowid
        conn.commit()
    logger.info(f"Logging application for {company}")
    return app_id


def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return applications as dicts, newest first, optionally filtered by status."""
    with get_connection() as conn:
        # Return rows that can be read by column name, so they convert cleanly to dicts
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute("SELECT * FROM applications WHERE status = ? ORDER BY id DESC", (status,))
        else:
            cursor.execute("SELECT * FROM applications ORDER BY id DESC")

        rows = cursor.fetchall()
    logger.info(f"Listing applications")
    return [dict(row) for row in rows]


def update_status(app_id: int, new_status: ApplicationStatus, notes: Optional[str] = None) -> bool:
    """Set an application's status, appending any new notes to the existing ones.

    Returns False if no application has the given ID.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()

        if notes:
            # "||" is SQL string concatenation: new notes go on a new line after
            # the old ones, so the history is kept rather than overwritten
            cursor.execute("""
                UPDATE applications 
                SET status = ?, last_updated = ?, notes = notes || '\n' || ?
                WHERE id = ?
            """, (new_status, now, notes, app_id))
        else:
            cursor.execute("""
                UPDATE applications 
                SET status = ?, last_updated = ?
                WHERE id = ?
            """, (new_status, now, app_id))

        # rowcount is 0 when the WHERE clause matched nothing, i.e. the ID doesn't exist
        updated = cursor.rowcount > 0
        conn.commit()
    return updated
