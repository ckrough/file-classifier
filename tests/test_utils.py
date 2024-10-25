import logging
import os
import sqlite3
import tempfile

import pytest

from src.ai_file_classifier.utils import (insert_or_update_file,
                                          is_supported_filetype)
from src.config.cache_config import DB_FILE, delete_cache

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Initialize the cache
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
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
    conn.close()
    yield
    # Teardown: Delete the cache file
    if os.path.exists(DB_FILE):
        delete_cache()


def test_is_supported_filetype():
    """
    Test if the file type is supported.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w',
                                     encoding='utf-8') as temp_txt_file:
        temp_txt_file.write("This is a sample text.")
        temp_txt_file_path = temp_txt_file.name

    try:
        # Test if the text file is supported
        assert is_supported_filetype(temp_txt_file_path) is True

        # Test if an unsupported file type returns False
        with tempfile.NamedTemporaryFile(delete=False,
                                         suffix=".unsupported",
                                         mode='w',
                                         encoding='utf-8') as temp_unsupported_file:
            temp_unsupported_file.write("This is an unsupported file type.")
            temp_unsupported_file_path = temp_unsupported_file.name
            assert is_supported_filetype(temp_unsupported_file_path) is False
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        # Clean up the temporary files
        if os.path.exists(temp_txt_file_path):
            os.remove(temp_txt_file_path)
        if os.path.exists(temp_unsupported_file_path):
            os.remove(temp_unsupported_file_path)


def test_insert_or_update_file():
    """
    Test inserting or updating a file record in the database.
    """
    file_path = "/path/to/sample.txt"
    suggested_name = "sample-suggested-name"
    category = "test-category"
    description = "test-description"
    vendor = "test-vendor"
    date = "20230101"

    try:
        insert_or_update_file(file_path, suggested_name,
                              category, description, vendor, date)

        # Verify that the record was inserted
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE file_path=?", (file_path,))
        record = cursor.fetchone()
        assert record is not None
        assert record[1] == file_path
        assert record[2] == suggested_name
        assert record[3] == category
        assert record[4] == description
        assert record[5] == vendor
        assert record[6] == date
        conn.close()
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    pytest.main()
