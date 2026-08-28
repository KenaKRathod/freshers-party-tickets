import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    STAFF_PASSWORD = os.environ.get('STAFF_PASSWORD', 'zenith2026')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    NUM_TICKETS = int(os.environ.get('NUM_TICKETS', '250'))

    # Turso cloud database (used in production)
    TURSO_DATABASE_URL = os.environ.get('TURSO_DATABASE_URL', '')
    TURSO_AUTH_TOKEN = os.environ.get('TURSO_AUTH_TOKEN', '')

    # Local SQLite fallback (used when Turso vars are not set)
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join('instance', 'tickets.db'))
