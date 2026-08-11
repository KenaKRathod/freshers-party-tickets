import os
import sqlite3
from datetime import datetime

from config import Config


def get_db():
    """Get a database connection with Row factory for dict-like access."""
    os.makedirs(os.path.dirname(Config.DATABASE_PATH) or '.', exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the tickets table and index if they don't exist."""
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            token         TEXT    UNIQUE NOT NULL,
            name          TEXT    DEFAULT '',
            checked_in    BOOLEAN DEFAULT 0,
            checked_in_at TEXT    NULL,
            created_at    TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_token ON tickets(token)')
    conn.commit()
    conn.close()


def get_ticket_by_token(token):
    """Look up a ticket by its URL token. Returns dict or None."""
    conn = get_db()
    row = conn.execute('SELECT * FROM tickets WHERE token = ?', (token,)).fetchone()
    conn.close()
    return dict(row) if row else None


def check_in_ticket(token):
    """Mark a ticket as checked in with the current timestamp."""
    conn = get_db()
    now = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
    conn.execute(
        'UPDATE tickets SET checked_in = 1, checked_in_at = ? WHERE token = ? AND checked_in = 0',
        (now, token)
    )
    conn.commit()
    conn.close()


def get_stats():
    """Return check-in statistics: total, checked_in, remaining."""
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM tickets').fetchone()[0]
    checked = conn.execute('SELECT COUNT(*) FROM tickets WHERE checked_in = 1').fetchone()[0]
    conn.close()
    return {
        'total': total,
        'checked_in': checked,
        'remaining': total - checked
    }


def get_all_tickets():
    """Return all tickets ordered by ID."""
    conn = get_db()
    rows = conn.execute('SELECT * FROM tickets ORDER BY id').fetchall()
    conn.close()
    return [dict(r) for r in rows]
