"""Unit tests for database operations."""

import sqlite3
from unittest import mock

import pytest

from src.storage.database import (
    connect_to_db,
    insert_or_update_file,
    get_all_suggested_changes,
)
from src.config.settings import DB_FILE


@mock.patch("sqlite3.connect")
def test_connect_to_db(mock_connect):
    """Test that connect_to_db calls sqlite3.connect with the correct DB_FILE."""
    connect_to_db()
    mock_connect.assert_called_once_with(DB_FILE)


@mock.patch("src.storage.database.connect_to_db")
def test_insert_or_update_file(mock_connect):
    """Test that insert_or_update_file correctly inserts or updates a file record."""
    mock_conn = mock.MagicMock()
    mock_connect.return_value = mock_conn

    file_path = "/path/to/file.txt"
    suggested_name = "new_file_name"
    metadata = {
        "category": "document",
        "description": "A test document",
        "vendor": "VendorX",
        "date": "2023-10-01",
    }

    insert_or_update_file(file_path, suggested_name, metadata)

    mock_connect.assert_called_once()
    mock_conn.cursor.assert_called_once()
    mock_cursor = mock_conn.cursor.return_value
    mock_cursor.execute.assert_called_once_with(
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
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


@mock.patch("src.storage.database.connect_to_db")
def test_insert_or_update_file_db_error(mock_connect):
    """Test that insert_or_update_file handles SQLite errors gracefully."""
    mock_connect.side_effect = sqlite3.Error("DB connection failed")

    file_path = "/path/to/file.txt"
    suggested_name = "new_file_name"
    metadata = {
        "category": "document",
        "description": "A test document",
        "vendor": "VendorX",
        "date": "2023-10-01",
    }

    with pytest.raises(sqlite3.Error):
        insert_or_update_file(file_path, suggested_name, metadata)


@mock.patch("src.storage.database.connect_to_db")
def test_get_all_suggested_changes(mock_connect):
    """Test that get_all_suggested_changes retrieves the correct data from the database."""
    mock_conn = mock.MagicMock()
    mock_cursor = mock.MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Simulate database rows
    mock_cursor.fetchall.return_value = [
        ("/path/to/file1.txt", "new_file1"),
        ("/path/to/file2.pdf", "new_file2"),
    ]

    changes = get_all_suggested_changes()

    mock_connect.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        """
            SELECT file_path, suggested_name
            FROM files
            WHERE suggested_name IS NOT NULL
        """
    )
    assert changes == [
        {"file_path": "/path/to/file1.txt", "suggested_name": "new_file1"},
        {"file_path": "/path/to/file2.pdf", "suggested_name": "new_file2"},
    ]


@mock.patch("src.storage.database.connect_to_db")
def test_get_all_suggested_changes_db_error(mock_connect):
    """Test that get_all_suggested_changes handles SQLite errors gracefully."""
    mock_connect.side_effect = sqlite3.Error("DB connection failed")

    changes = get_all_suggested_changes()

    assert changes == []
