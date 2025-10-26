"""
This module contains unit tests for the file inventory module.
"""

import logging
import os
import sqlite3

import pytest

from src.storage.cache import initialize_cache, delete_cache
from src.config.settings import DB_FILE

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Set up and tear down the test environment."""
    initialize_cache()
    yield
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
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
    table = cursor.fetchone()
    assert table is not None
    conn.close()


if __name__ == "__main__":
    pytest.main()
