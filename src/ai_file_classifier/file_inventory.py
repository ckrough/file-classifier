import logging
import sqlite3

from src.ai_file_classifier.config import DB_FILE

logger = logging.getLogger(__name__)


def initialize_cache() -> None:
    """
    Initializes the SQLite cache database, creating the necessary
    table if it does not exist.
    """
    try:
        conn: sqlite3.Connection = sqlite3.connect(DB_FILE)
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE,
                category TEXT,
                description TEXT,
                vendor TEXT,
                date TEXT,
                suggested_name TEXT
            )
        ''')
        conn.commit()
        logger.debug("Cache database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing cache database: {e}", exc_info=True)
    finally:
        conn.close()
