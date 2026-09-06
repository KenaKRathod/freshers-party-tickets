"""
Migrate tokens from local SQLite database to Turso cloud database.
Uses Turso's HTTP API — no native compilation required.

Usage:
    python migrate_to_turso.py
"""

import os
import sqlite3
import requests
from config import Config


def get_turso_url():
    """Convert libsql:// URL to https:// for HTTP API."""
    url = os.environ.get('TURSO_DATABASE_URL', '')
    return url.replace('libsql://', 'https://')


def main():
    turso_url = get_turso_url()
    turso_token = os.environ.get('TURSO_AUTH_TOKEN', '')

    if not turso_url or not turso_token:
        print("ERROR: Set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN environment variables first!")
        return

    # Read tokens from local SQLite
    local_db = Config.DATABASE_PATH
    if not os.path.exists(local_db):
        print(f"ERROR: Local database not found at {local_db}")
        print("Run 'python generate.py' first to create tokens locally.")
        return

    conn = sqlite3.connect(local_db)
    rows = conn.execute('SELECT token, name FROM tickets ORDER BY id').fetchall()
    conn.close()

    print(f"Found {len(rows)} tokens in local database.")
    if not rows:
        return

    # Create table in Turso
    headers = {
        'Authorization': f'Bearer {turso_token}',
        'Content-Type': 'application/json'
    }

    # Step 1: Create table
    print("Creating table in Turso...")
    resp = requests.post(f"{turso_url}/v2/pipeline", headers=headers, json={
        "requests": [
            {
                "type": "execute",
                "stmt": {
                    "sql": """CREATE TABLE IF NOT EXISTS tickets (
                        id            INTEGER PRIMARY KEY AUTOINCREMENT,
                        token         TEXT    UNIQUE NOT NULL,
                        name          TEXT    DEFAULT '',
                        checked_in    INTEGER DEFAULT 0,
                        checked_in_at TEXT    NULL,
                        created_at    TEXT    DEFAULT (datetime('now', 'localtime'))
                    )"""
                }
            },
            {
                "type": "execute",
                "stmt": {"sql": "CREATE INDEX IF NOT EXISTS idx_token ON tickets(token)"}
            },
            {"type": "close"}
        ]
    })

    if resp.status_code != 200:
        print(f"ERROR creating table: {resp.status_code} - {resp.text}")
        return
    print("  Table created OK.")

    # Step 2: Insert tokens in batches of 20
    batch_size = 20
    total_inserted = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        requests_list = []

        for token, name in batch:
            requests_list.append({
                "type": "execute",
                "stmt": {
                    "sql": "INSERT OR IGNORE INTO tickets (token, name) VALUES (?, ?)",
                    "args": [
                        {"type": "text", "value": token},
                        {"type": "text", "value": name or ""}
                    ]
                }
            })

        requests_list.append({"type": "close"})

        resp = requests.post(f"{turso_url}/v2/pipeline", headers=headers, json={
            "requests": requests_list
        })

        if resp.status_code != 200:
            print(f"ERROR inserting batch {i}: {resp.status_code} - {resp.text}")
            return

        total_inserted += len(batch)
        print(f"  Inserted {total_inserted}/{len(rows)} tokens...")

    print(f"\nDone! {total_inserted} tokens migrated to Turso cloud database.")
    print("Refresh your dashboard to see them.")


if __name__ == '__main__':
    main()
