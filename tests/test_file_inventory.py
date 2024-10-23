import logging
import os
import sqlite3
import tempfile

import pytest

from src.ai_file_classifier.config import DB_FILE, delete_cache
from src.ai_file_classifier.file_inventory import (initialize_cache,
                                                   inventory_files)

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Initialize the cache
    initialize_cache()
    yield
    # Teardown: Delete the cache file
    if os.path.exists(DB_FILE):
        delete_cache()


def test_initialize_cache():
    """
    Test that the cache database is initialized correctly.
    """
    initialize_cache()
    assert os.path.exists(DB_FILE)

    # Verify that the required table exists
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
    table = cursor.fetchone()
    assert table is not None
    conn.close()


def test_inventory_files():
    """
    Test that files in a directory are inventoried and stored in the database.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample text and PDF files
        txt_file_path = os.path.join(temp_dir, "sample.txt")
        pdf_file_path = os.path.join(temp_dir, "sample.pdf")

        with open(txt_file_path, "w") as txt_file:
            txt_file.write("This is a sample text file.")

        with open(pdf_file_path, "w") as pdf_file:
            pdf_file.write("This is a sample PDF file.")

        # Inventory the files in the temporary directory
        inventory_files(temp_dir)

        # Verify that the files are stored in the database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_path FROM files WHERE file_path=?", (txt_file_path,))
        txt_record = cursor.fetchone()
        assert txt_record is not None

        cursor.execute(
            "SELECT file_path FROM files WHERE file_path=?", (pdf_file_path,))
        pdf_record = cursor.fetchone()
        assert pdf_record is not None
        conn.close()


if __name__ == "__main__":
    pytest.main()
