import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "cricbuzz.db"

def get_db_connection():
    """Creates and returns a connection to the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_connection():
    # Set a 30-second timeout so SQLite waits instead of instantly failing
    conn = sqlite3.connect('cricbuzz.db', timeout=30.0)
    # Enable WAL mode for high-concurrency read/write operations
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# Alias so pages importing either name work seamlessly
get_connection = get_db_connection