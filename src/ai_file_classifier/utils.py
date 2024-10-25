"""Utility functions for the AI File Classifier application."""

import argparse
import hashlib
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

import magic

from src.ai_file_classifier.file_analyzer import analyze_file_content
from src.config.cache_config import DB_FILE

logger = logging.getLogger(__name__)


def get_user_arguments() -> argparse.Namespace:
    """
    Parses command line arguments provided by the user.
    """
    parser = argparse.ArgumentParser(description="File Analyzer Application")
    parser.add_argument(
        "path", type=str, help="Path to the file or directory to be analyzed"
    )
    parser.add_argument(
        "--auto-rename", action="store_true", help="Always rename the file[s]"
    )
    return parser.parse_args()


def is_supported_filetype(file_path: str) -> bool:
    """
    Validate if the specified file is a supported type.

    Args:
        file_path (str): Path to the file to be checked.

    Returns:
        bool: True if the file type is supported, False otherwise.
    """
    supported_mimetypes: List[str] = ["text/plain", "application/pdf"]
    try:
        mime = magic.Magic(mime=True)
        mimetype: str = mime.from_file(file_path)
        logger.debug("Detected MIME type for file '%s': %s",
                     file_path, mimetype)
        return mimetype in supported_mimetypes
    except ImportError:
        logger.error("Failed to import 'magic' module", exc_info=True)
        return False
    except (IOError, OSError) as e:
        logger.error("Error accessing file '%s': %s", file_path, str(e),
                     exc_info=True)
        return False


def calculate_md5(file_path: str) -> Optional[str]:
    """
    Calculates the MD5 hash of the given file.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except (IOError, OSError) as e:
        logger.error("Error reading file '%s': %s", file_path, str(e),
                     exc_info=True)
        return None
    return hash_md5.hexdigest()


def connect_to_db() -> sqlite3.Connection:
    """
    Connects to the SQLite database and returns the connection object.
    """
    return sqlite3.connect(DB_FILE)


def insert_or_update_file(
    file_path: str,
    suggested_name: str,
    category: Optional[str] = None,
    description: Optional[str] = None,
    vendor: Optional[str] = None,
    date: Optional[str] = None
) -> None:
    """
    Insert or update a file record in the cache with the given metadata.

    Args:
        file_path (str): Path to the file.
        suggested_name (str): Suggested name for the file.
        category (Optional[str]): File category.
        description (Optional[str]): File description.
        vendor (Optional[str]): File vendor.
        date (Optional[str]): File date.
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_to_db()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO files (
                file_path, suggested_name, category, description, vendor, date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_path, suggested_name, category, description, vendor, date))
        conn.commit()
        logger.debug(
            "File '%s' cache updated with suggested name '%s'.",
            file_path,
            suggested_name
        )
    except sqlite3.Error as e:
        logger.error(
            "SQLite error inserting or updating file '%s': %s",
            file_path,
            str(e),
            exc_info=True
        )
    finally:
        if conn:
            conn.close()


def get_all_suggested_changes() -> List[Dict[str, str]]:
    """
    Retrieves all files with suggested changes from the SQLite database.
    """
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = connect_to_db()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute('''
            SELECT file_path, suggested_name
            FROM files
            WHERE suggested_name IS NOT NULL
        ''')
        changes: List[Dict[str, str]] = [{'file_path': row[0],
                                          'suggested_name': row[1]}
                                         for row in cursor.fetchall()]
        logger.debug("Retrieved %d suggested changes from cache.",
                     len(changes))
        return changes
    except sqlite3.Error as e:
        logger.error("SQLite error retrieving suggested changes: %s", str(e),
                     exc_info=True)
        return []
    finally:
        if conn:
            conn.close()


def rename_files(suggested_changes: List[Dict[str, str]]) -> None:
    """
    Renames files in bulk based on the approved suggested changes.
    """
    for change in suggested_changes:
        file_path: str = change['file_path']
        suggested_name: str = change['suggested_name']
        try:
            _, ext = os.path.splitext(file_path)
            directory: str = os.path.dirname(file_path)
            new_path: str = os.path.join(directory, f"{suggested_name}{ext}")
            os.rename(file_path, new_path)
            logger.info("File '%s' renamed to '%s'.", file_path, new_path)
        except (OSError, IOError) as e:
            logger.error("Error renaming file '%s' to '%s': %s",
                         file_path, suggested_name, str(e), exc_info=True)


def process_file(file_path: str, model: str, client: Any) -> None:
    """
    Processes a single file by analyzing its content and caching metadata.
    """
    if not os.path.exists(file_path):
        logger.error("The file '%s' does not exist.", file_path)
        return

    if not os.path.isfile(file_path):
        logger.error("The path '%s' is not a file.", file_path)
        return

    if not is_supported_filetype(file_path):
        logger.error("The file '%s' is not a supported file type.", file_path)
        return

    try:
        suggested_name, category, vendor, description, \
            date = analyze_file_content(file_path, model, client)
        if suggested_name:
            logger.info("Suggested name for the file: %s", suggested_name)
            insert_or_update_file(file_path, suggested_name,
                                  category, description, vendor, date)
        else:
            logger.error("Could not determine a suitable name for the file.")
    except RuntimeError as e:
        logger.error(str(e))
