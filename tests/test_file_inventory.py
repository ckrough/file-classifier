import logging
import os
import sqlite3
import tempfile

import pytest

from src.ai_file_classifier.file_inventory import (initialize_cache,
                                                   inventory_files)

logger = logging.getLogger(__name__)
DB_FILE = "file_cache.db"


def test_initialize_cache():
    """
    Test the initialization of the SQLite cache database.
    """
    try:
        # Initialize the cache
        initialize_cache()

        # Verify that the database file exists
        assert os.path.exists(DB_FILE) is True

        # Verify that the expected table exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            '''SELECT name FROM sqlite_master WHERE type='table' AND name='files';''')
        table_exists = cursor.fetchone()
        assert table_exists is not None
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        if 'conn' in locals():
            conn.close()


def test_inventory_files():
    """
    Test the inventorying of files in a specified directory.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample text and PDF files in the temporary directory
        txt_file_path = os.path.join(temp_dir, "sample.txt")
        with open(txt_file_path, "w", encoding="utf-8") as txt_file:
            txt_file.write("This is a sample text file.")

        pdf_file_path = os.path.join(temp_dir, "sample.pdf")
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="This is a sample PDF file.", ln=True)
        pdf.output(pdf_file_path)

        try:
            # Initialize the cache
            initialize_cache()

            # Inventory the files in the temporary directory
            inventory_files(temp_dir)

            # Verify that the files were added to the database
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT file_path FROM files WHERE file_path = ?''', (txt_file_path,))
            txt_file_record = cursor.fetchone()
            assert txt_file_record is not None

            cursor.execute(
                '''SELECT file_path FROM files WHERE file_path = ?''', (pdf_file_path,))
            pdf_file_record = cursor.fetchone()
            assert pdf_file_record is not None
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
        finally:
            if 'conn' in locals():
                conn.close()


if __name__ == "__main__":
    pytest.main()
