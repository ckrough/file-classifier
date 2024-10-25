"""
This module contains unit tests for the file inventory module.
"""

import logging
import os
import sqlite3

import pytest

from src.config.cache_config import DB_FILE, delete_cache
from src.ai_file_classifier.file_inventory import initialize_cache

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


if __name__ == "__main__":
    pytest.main()
