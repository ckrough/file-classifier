"""
Database operations for file analysis caching.

This module provides functions for interacting with the SQLite database,
including connection management, inserting/updating records, and querying data.
"""

import logging
import sqlite3
from typing import Optional

from src.config.settings import DB_FILE

logger = logging.getLogger(__name__)


def connect_to_db() -> sqlite3.Connection:
    """
    Connect to the SQLite database and return the connection object.

    Returns:
        sqlite3.Connection: The SQLite database connection object.
    """
    return sqlite3.connect(DB_FILE)


def insert_or_update_file(
    file_path: str, suggested_name: str, metadata: dict[str, Optional[str]]
) -> None:
    """
    Insert or update a file record in the cache with the given metadata.

    Args:
        file_path (str): Path to the file.
        suggested_name (str): Suggested name for the file.
        metadata (dict[str, Optional[str]]): Dictionary containing additional
            metadata fields (category, description, vendor, date).

    Returns:
        None
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_to_db()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO files (
                file_path, suggested_name, category, description, vendor, date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                file_path,
                suggested_name,
                metadata.get("category"),
                metadata.get("description"),
                metadata.get("vendor"),
                metadata.get("date"),
            ),
        )
        conn.commit()
        logger.debug(
            "File '%s' cache updated with suggested name '%s'.",
            file_path,
            suggested_name,
        )
    except sqlite3.Error as e:
        logger.error(
            "SQLite error inserting or updating file '%s': %s",
            file_path,
            str(e),
            exc_info=True,
        )
        raise
    finally:
        if conn:
            conn.close()


def get_all_suggested_changes() -> list[dict[str, str]]:
    """
    Retrieve all files with suggested changes from the SQLite database.

    Returns:
        list[dict[str, str]]: A list of dictionaries containing file paths and suggested names.
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_to_db()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute(
            """
            SELECT file_path, suggested_name
            FROM files
            WHERE suggested_name IS NOT NULL
        """
        )
        changes: list[dict[str, str]] = [
            {"file_path": row[0], "suggested_name": row[1]} for row in cursor.fetchall()
        ]
        logger.debug("Retrieved %d suggested changes from cache.", len(changes))
        return changes
    except sqlite3.Error as e:
        logger.error(
            "SQLite error retrieving suggested changes: %s", str(e), exc_info=True
        )
        return []
    finally:
        if conn:
            conn.close()
