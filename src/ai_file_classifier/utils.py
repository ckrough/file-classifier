"""
Utility functions for the AI File Classifier application.

This module provides a suite of helper functions that facilitate file analysis,
caching, and file operations. It includes functionalities such as parsing user
arguments, validating file types, calculating file hashes, interacting with the
SQLite database, and renaming files based on suggested changes.

Functions:
    get_user_arguments: Parses command line arguments provided by the user.
    is_supported_filetype: Validates if a file is of a supported type.
    calculate_md5: Calculates the MD5 hash of a given file.
    connect_to_db: Connects to the SQLite database.
    insert_or_update_file: Inserts or updates file records in the cache.
    get_all_suggested_changes: Retrieves all files with suggested name changes.
    rename_files: Renames files based on approved suggested changes.
    process_file: Processes a single file by analyzing its content and caching metadata.
"""

import argparse
import hashlib
import logging
import os
import sqlite3
from typing import Dict, List, Optional

import magic

from src.ai_file_classifier.file_analyzer import analyze_file_content
from src.config.cache_config import DB_FILE

from src.ai_file_classifier.ai_client import AIClient

__all__ = [
    "get_user_arguments",
    "is_supported_filetype",
    "calculate_md5",
    "connect_to_db",
    "insert_or_update_file",
    "get_all_suggested_changes",
    "rename_files",
    "process_file",
]

logger = logging.getLogger(__name__)


def get_user_arguments() -> argparse.Namespace:
    """
    Parses command line arguments provided by the user.

    Args:
        None

    Returns:
        argparse.Namespace: The parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="File Analyzer Application")
    parser.add_argument(
        "path", type=str, help="Path to the file or directory to be analyzed"
    )
    parser.add_argument(
        "--auto-rename", action="store_true", help="Always rename the file[s]"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute a dry run without renaming files",
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
        logger.debug("Detected MIME type for file '%s': %s", file_path, mimetype)
        return mimetype in supported_mimetypes
    except ImportError:
        logger.error("Failed to import 'magic' module", exc_info=True)
        return False
    except (IOError, OSError) as e:
        logger.error("Error accessing file '%s': %s", file_path, str(e), exc_info=True)
        return False


def calculate_md5(file_path: str) -> Optional[str]:
    """
    Calculates the MD5 hash of the given file.

    Args:
        file_path (str): Path to the file.

    Returns:
        Optional[str]: The MD5 hash of the file, or None if an error occurs.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
    except (IOError, OSError) as e:
        logger.error("Error reading file '%s': %s", file_path, str(e), exc_info=True)
        return None
    return hash_md5.hexdigest()


def connect_to_db() -> sqlite3.Connection:
    """
    Connects to the SQLite database and returns the connection object.

    Returns:
        sqlite3.Connection: The SQLite database connection object.
    """
    return sqlite3.connect(DB_FILE)


def insert_or_update_file(
    file_path: str, suggested_name: str, metadata: Dict[str, Optional[str]]
) -> None:
    """
    Insert or update a file record in the cache with the given metadata.

    Args:
        file_path (str): Path to the file.
        suggested_name (str): Suggested name for the file.
        metadata (Dict[str, Optional[str]]): Dictionary containing additional
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
            suggested_name
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


def get_all_suggested_changes() -> List[Dict[str, str]]:
    """
    Retrieves all files with suggested changes from the SQLite database.

    Returns:
        List[Dict[str, str]]: A list of dictionaries containing file paths and suggested names.
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
        changes: List[Dict[str, str]] = [
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


def rename_files(suggested_changes: List[Dict[str, str]]) -> None:
    """
    Renames files in bulk based on the approved suggested changes.
    File extensions are preserved from the original filename.

    Args:
        suggested_changes (List[Dict[str, str]]): A list of dictionaries containing file paths and suggested names.

    Returns:
        None
    """
    for change in suggested_changes:
        file_path: str = change["file_path"]
        suggested_name: str = change["suggested_name"]
        try:
            # Extract extension from original file path
            _, ext = os.path.splitext(file_path)

            # Defensive check: ensure we have an extension for supported files
            if not ext:
                logger.warning(
                    "File '%s' has no extension. This may indicate an issue.",
                    file_path
                )

            directory: str = os.path.dirname(file_path)
            new_path: str = os.path.join(directory, f"{suggested_name}{ext}")

            logger.debug(
                "Renaming '%s' to '%s' (extension: '%s')",
                file_path,
                new_path,
                ext
            )

            os.rename(file_path, new_path)
            logger.info("File '%s' renamed to '%s'.", file_path, new_path)
        except (OSError, IOError) as e:
            logger.error(
                "Error renaming file '%s' to '%s': %s",
                file_path,
                suggested_name,
                str(e),
                exc_info=True,
            )
            raise


def process_file(file_path: str, model: str, client: AIClient) -> None:
    """
    Processes a single file by analyzing its content and caching metadata.

    Args:
        file_path (str): Path to the file.
        model (str): The model to use for file analysis.
        client (AIClient): The AI client used for file analysis.

    Returns:
        None
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
        suggested_name, category, vendor, description, date = analyze_file_content(
            file_path, model, client
        )
        if suggested_name:
            logger.info("Suggested name for the file: %s", suggested_name)
            metadata = {
                "category": category,
                "description": description,
                "vendor": vendor,
                "date": date,
            }
            insert_or_update_file(file_path, suggested_name, metadata)
        else:
            logger.error("Could not determine a suitable name for the file.")
    except RuntimeError as e:
        logger.error(str(e))
        raise
