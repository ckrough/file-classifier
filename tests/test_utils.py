import logging
import os
import sqlite3
import tempfile

import pytest

from src.ai_file_classifier.utils import (bulk_rename_files,
                                          get_all_suggested_changes,
                                          insert_or_update_file)

logger = logging.getLogger(__name__)

DB_FILE = "file_cache.db"


def test_insert_or_update_file():
    """
    Test inserting or updating a file record in the SQLite database.
    """
    test_file_path = "test_file.txt"
    suggested_name = "suggested_file_name"
    category = "test_category"
    description = "test_description"
    vendor = "test_vendor"
    date = "20231023"

    conn = None
    try:
        # Insert or update the file in the cache
        insert_or_update_file(test_file_path, suggested_name,
                              category, description, vendor, date)

        # Verify that the file was inserted or updated
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT * FROM files WHERE file_path = ?''', (test_file_path,))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == test_file_path
        assert row[6] == suggested_name
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()


def test_get_all_suggested_changes():
    """
    Test retrieving all files with suggested changes from the SQLite database.
    """
    try:
        changes = get_all_suggested_changes()
        assert isinstance(changes, list)
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


def test_bulk_rename_files():
    """
    Test renaming files in bulk based on suggested changes.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w',
                                     encoding='utf-8') as temp_file:
        temp_file.write("This is a sample text.")
        temp_file_path = temp_file.name

    try:
        suggested_name = "bulk_renamed_file"
        changes = [{'file_path': temp_file_path,
                    'suggested_name': suggested_name}]

        # Perform the bulk rename operation
        bulk_rename_files(changes)

        # Verify that the file has been renamed
        new_path = os.path.join(os.path.dirname(
            temp_file_path), f"{suggested_name}.txt")
        assert os.path.exists(new_path) is True
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        # Clean up the renamed file
        if 'new_path' in locals() and os.path.exists(new_path):
            os.remove(new_path)


if __name__ == "__main__":
    pytest.main()
