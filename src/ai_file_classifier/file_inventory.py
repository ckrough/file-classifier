"""
Module for managing file inventory and cache operations.

This module handles the initialization and management of the SQLite cache database.
It provides functions to create necessary tables and ensure the cache is properly set up.
Logging is utilized to track the initialization process and handle any errors that may occur.
"""

import logging
import sqlite3

from src.config.cache_config import DB_FILE

CREATE_FILES_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY,
        file_path TEXT UNIQUE,
        category TEXT,
        description TEXT,
        vendor TEXT,
        date TEXT,
        suggested_name TEXT
    )
'''

logger = logging.getLogger(__name__)


def initialize_cache() -> None:
    """
    Initializes the SQLite cache database, creating the necessary
    table if it does not exist.
    """
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute(CREATE_FILES_TABLE_SQL)
            conn.commit()
            logger.debug("Cache database initialized successfully.")
    except sqlite3.Error as e:
        logger.error("Error initializing cache database (%s): %s", DB_FILE, e, exc_info=True)
