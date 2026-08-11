import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    STAFF_PASSWORD = os.environ.get('STAFF_PASSWORD', 'zenith2026')
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join('instance', 'tickets.db'))
    NUM_TICKETS = int(os.environ.get('NUM_TICKETS', '250'))
