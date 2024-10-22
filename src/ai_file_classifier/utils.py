import argparse
import hashlib
import logging
import os
import sqlite3

logger = logging.getLogger(__name__)


def get_user_arguments():
    """
    Parses command line arguments provided by the user.
    """
    parser = argparse.ArgumentParser(description="File Analyzer Application")
    parser.add_argument(
        "--file_path", type=str, help="Path to the file to be analyzed"
    )
    parser.add_argument(
        "--directory", type=str, help="Path to the directory to be analyzed"
    )
    parser.add_argument(
        "--auto-rename", action="store_true", help="Always rename the file"
    )
    return parser.parse_args()


def is_supported_filetype(file_path):
    """
    Validates if the specified file is a supported type.
    """
    supported_mimetypes = ["text/plain", "application/pdf"]
    try:
        import magic
        mime = magic.Magic(mime=True)
        mimetype = mime.from_file(file_path)
        logger.debug(f"Detected MIME type for file '{file_path}': {mimetype}")
        return mimetype in supported_mimetypes
    except Exception as e:
        logger.error(f"Error detecting MIME type for file '{
                     file_path}': {e}", exc_info=True)
        return False


def rename_file(file_path, new_name):
    """
    Renames the specified file to the new name, preserving the file extension.
    """
    try:
        base, ext = os.path.splitext(file_path)
        directory = os.path.dirname(file_path)
        new_path = os.path.join(directory, f"{new_name}{ext}")
        os.rename(file_path, new_path)
        logger.info(f"File '{file_path}' renamed to '{new_path}'")
    except Exception as e:
        logger.error(f"Error renaming file '{file_path}' to '{
                     new_name}': {e}", exc_info=True)


DB_FILE = "file_cache.db"


def calculate_md5(file_path):
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


def connect_to_db():
    """
    Connects to the SQLite database and returns the connection object.
    """
    return sqlite3.connect(DB_FILE)


def insert_or_update_file(file_path, file_hash, category=None,
                          description=None):
    """
    Inserts or updates a file record in the SQLite database.
    """
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO files (
                   file_path, file_hash, category, description
                   )
        VALUES (?, ?, ?, ?)
    ''', (file_path, file_hash, category, description))
    conn.commit()
    conn.close()
