import os
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from contextlib import contextmanager

# Set up logger for db 
logger = logging.getLogger(__name__)

# Anchor DB_PATH to the exact directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobops.db")

@contextmanager
def get_connection():
    """Yield a sqlite3 connection, guaranteeing it's closed even if an
    exception is raised while it's in use."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

# Define application status options to be used
class ApplicationStatus(str, Enum):
    APPLIED = "Applied"
    SCREENING = "Screen scheduled"
    INTERVIEWING = "Interviewing"
    OFFER = "Offer received"
    REJECTED = "Rejected"

def init_db():
    """Initialize the SQLite database with the applications table."""
    logger.info("Initializing SQLite database...")
    with get_connection() as conn:
        cursor = conn.cursor()
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (company, role, status, date_applied, last_updated, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (company, role, ApplicationStatus.APPLIED.value, now, now, notes))
        app_id = cursor.lastrowid
        conn.commit()
    logger.info(f"Logging application for {company}")
    return app_id

def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        cursor = conn.cursor()
        if notes:
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

        updated = cursor.rowcount > 0
        conn.commit()
    return updated