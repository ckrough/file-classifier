import logging
import os
import sqlite3
from typing import Generator

from src.ai_file_classifier.config import DB_FILE
from src.ai_file_classifier.utils import calculate_md5

# Configure logging
logging.basicConfig(level=logging.DEBUG)
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
                file_hash TEXT,
                category TEXT,
                description TEXT,
                vendor TEXT,
                date TEXT,
                suggested_name TEXT
            )
        ''')
        conn.commit()
        logger.info("Cache database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing cache database: {e}", exc_info=True)
    finally:
        conn.close()


def inventory_files(directory: str) -> Generator[str, None, None]:
    """
    Traverses the specified directory and inventories all .txt and .pdf files,
    storing their paths and MD5 hashes in the SQLite database.
    """
    try:
        conn: sqlite3.Connection = sqlite3.connect(DB_FILE)
        cursor: sqlite3.Cursor = conn.cursor()

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(('.txt', '.pdf')):
                    file_path: str = os.path.join(root, file)
                    file_hash: str = calculate_md5(file_path)

                    # Insert or update the file record if the file hash differs
                    cursor.execute('''
                        INSERT OR REPLACE INTO files (file_path, file_hash)
                        VALUES (?, ?)
                    ''', (file_path, file_hash))
                    logger.info(
                        f"File '{file_path}' "
                        f"inventoried with hash '{file_hash}'.")

        conn.commit()
        logger.info(f"Inventory completed for directory: {directory}")
    except Exception as e:
        logger.error(f"Error during file inventory: {e}", exc_info=True)
    finally:
        conn.close()
