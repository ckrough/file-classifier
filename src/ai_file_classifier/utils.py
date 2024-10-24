import argparse
import hashlib
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

from src.ai_file_classifier.config import DB_FILE
from src.ai_file_classifier.file_analyzer import analyze_file_content

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
    Validates if the specified file is a supported type.
    """
    supported_mimetypes: List[str] = ["text/plain", "application/pdf"]
    try:
        import magic
        mime = magic.Magic(mime=True)
        mimetype: str = mime.from_file(file_path)
        logger.debug(f"Detected MIME type for file '{file_path}': {mimetype}")
        return mimetype in supported_mimetypes
    except Exception as e:
        logger.error(f"Error detecting MIME type for file '{
                     file_path}': {e}", exc_info=True)
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
    except Exception as e:
        logger.error(f"Error calculating MD5 for file '{
                     file_path}': {e}", exc_info=True)
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
    Inserts or updates a file record in the cache with the given metadata.
    """
    try:
        conn: sqlite3.Connection = connect_to_db()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO files (
                file_path, suggested_name, category, description, vendor, date
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (file_path, suggested_name, category, description, vendor, date))
        conn.commit()
        logger.info(f"File '{file_path}' cache updated with suggested name '{
                    suggested_name}'.")
    except Exception as e:
        logger.error(f"Error inserting or updating file '{
                     file_path}': {e}", exc_info=True)
    finally:
        conn.close()


def get_all_suggested_changes() -> List[Dict[str, str]]:
    """
    Retrieves all files with suggested changes from the SQLite database.
    """
    try:
        conn: sqlite3.Connection = connect_to_db()
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute('''
            SELECT file_path, suggested_name
            FROM files
            WHERE suggested_name IS NOT NULL
        ''')
        changes: List[Dict[str, str]] = [{'file_path': row[0],
                                          'suggested_name': row[1]}
                                         for row in cursor.fetchall()]
        logger.info(f"Retrieved {len(changes)} suggested changes from cache.")
        return changes
    except Exception as e:
        logger.error(f"Error retrieving suggested changes: {e}", exc_info=True)
        return []
    finally:
        conn.close()


def rename_files(suggested_changes: List[Dict[str, str]]) -> None:
    """
    Renames files in bulk based on the approved suggested changes.
    """
    for change in suggested_changes:
        file_path: str = change['file_path']
        suggested_name: str = change['suggested_name']
        try:
            base, ext = os.path.splitext(file_path)
            directory: str = os.path.dirname(file_path)
            new_path: str = os.path.join(directory, f"{suggested_name}{ext}")
            os.rename(file_path, new_path)
            logger.info(f"File '{file_path}' renamed to '{new_path}'.")
        except Exception as e:
            logger.error(f"Error renaming file '{file_path}' to '{
                         suggested_name}': {e}", exc_info=True)


def process_file(file_path: str, model: str, client: Any,
                 logger: logging.Logger) -> None:
    """
    Processes a single file by analyzing its content and caching metadata.
    """
    if not os.path.exists(file_path):
        logger.error(f"The file '{file_path}' does not exist.")
        return

    if not os.path.isfile(file_path):
        logger.error(f"The path '{file_path}' is not a file.")
        return

    if not is_supported_filetype(file_path):
        logger.error(f"The file '{file_path}' is not a supported file type.")
        return

    try:
        suggested_name, category, vendor, description, \
            date = analyze_file_content(file_path, model, client)
        if suggested_name:
            logger.info(f"Suggested name for the file: {suggested_name}")
            insert_or_update_file(file_path, suggested_name,
                                  category, description, vendor, date)
        else:
            logger.error("Could not determine a suitable name for the file.")
    except RuntimeError as e:
        logger.error(str(e))
