import os
import sqlite3
from datetime import datetime, timezone, timedelta

# IST is UTC+5:30 — ensures correct timestamps regardless of server timezone
IST = timezone(timedelta(hours=5, minutes=30))

from config import Config

# ---------------------------------------------------------------------------
# Choose database driver: Turso (cloud) or local SQLite
# ---------------------------------------------------------------------------
_USE_TURSO = bool(Config.TURSO_DATABASE_URL and Config.TURSO_AUTH_TOKEN)

if _USE_TURSO:
    try:
        import libsql_experimental as libsql
    except ImportError:
        _USE_TURSO = False
        print("  [INFO] libsql_experimental not installed — using local SQLite")


def get_db():
    """Get a database connection. Uses Turso if configured, else local SQLite."""
    if _USE_TURSO:
        conn = libsql.connect(
            database=Config.TURSO_DATABASE_URL,
            auth_token=Config.TURSO_AUTH_TOKEN
        )
    else:
        os.makedirs(os.path.dirname(Config.DATABASE_PATH) or '.', exist_ok=True)
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row, columns):
    """Convert a database row to a dict. Handles both sqlite3.Row and tuple."""
    if row is None:
        return None
    try:
        return dict(row)
    except (TypeError, ValueError):
        return dict(zip(columns, row))


# Column names for the tickets table
_TICKET_COLS = ['id', 'token', 'name', 'checked_in', 'checked_in_at', 'created_at']


def init_db():
    """Create the tickets table and index if they don't exist."""
    conn = get_db()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                token         TEXT    UNIQUE NOT NULL,
                name          TEXT    DEFAULT '',
                checked_in    INTEGER DEFAULT 0,
                checked_in_at TEXT    NULL,
                created_at    TEXT    DEFAULT (datetime('now', 'localtime'))
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_token ON tickets(token)')
        conn.commit()
    finally:
        conn.close()


def get_ticket_by_token(token):
    """Look up a ticket by its URL token. Returns dict or None."""
    conn = get_db()
    try:
        row = conn.execute('SELECT * FROM tickets WHERE token = ?', (token,)).fetchone()
        return _row_to_dict(row, _TICKET_COLS)
    finally:
        conn.close()


def check_in_ticket(token):
    """Mark a ticket as checked in with the current timestamp."""
    conn = get_db()
    try:
        now = datetime.now(IST).strftime('%Y-%m-%d %I:%M:%S %p')
        conn.execute(
            'UPDATE tickets SET checked_in = 1, checked_in_at = ? WHERE token = ? AND checked_in = 0',
            (now, token)
        )
        conn.commit()
    finally:
        conn.close()


def get_stats():
    """Return check-in statistics: total, checked_in, remaining."""
    conn = get_db()
    try:
        total = conn.execute('SELECT COUNT(*) FROM tickets').fetchone()[0]
        checked = conn.execute('SELECT COUNT(*) FROM tickets WHERE checked_in = 1').fetchone()[0]
        return {
            'total': total,
            'checked_in': checked,
            'remaining': total - checked
        }
    finally:
        conn.close()


def get_all_tickets():
    """Return all tickets ordered by ID."""
    conn = get_db()
    try:
        rows = conn.execute('SELECT * FROM tickets ORDER BY id').fetchall()
        return [_row_to_dict(r, _TICKET_COLS) for r in rows]
    finally:
        conn.close()


def undo_check_in(token):
    """Reverse a check-in — reset checked_in to 0 and clear timestamp."""
    conn = get_db()
    try:
        conn.execute(
            'UPDATE tickets SET checked_in = 0, checked_in_at = NULL WHERE token = ? AND checked_in = 1',
            (token,)
        )
        conn.commit()
    finally:
        conn.close()

