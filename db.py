import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

# Anchor DB_PATH to the exact directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "jobops.db")

def init_db():
    """Initialize the SQLite database with the applications table."""
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()

def add_application(company: str, role: str, notes: str = "") -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO applications (company, role, status, date_applied, last_updated, notes)
        VALUES (?, ?, 'Applied', ?, ?, ?)
    """, (company, role, now, now, notes))
    app_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return app_id

def list_applications(status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if status:
        cursor.execute("SELECT * FROM applications WHERE status = ? ORDER BY id DESC", (status,))
    else:
        cursor.execute("SELECT * FROM applications ORDER BY id DESC")
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_status(app_id: int, new_status: str, notes: Optional[str] = None) -> bool:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
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
    conn.close()
    return updated