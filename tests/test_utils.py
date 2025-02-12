"""Unit tests for the utils module."""

import hashlib
import logging
import os
import sys
import tempfile
import shutil
import sqlite3
from unittest import mock

import pytest

from src.ai_file_classifier.utils import (
    get_user_arguments,
    is_supported_filetype,
    calculate_md5,
    connect_to_db,
    insert_or_update_file,
    get_all_suggested_changes,
    rename_files,
    process_file,
)
from src.config.cache_config import DB_FILE
from src.ai_file_classifier.file_analyzer import analyze_file_content

logger = logging.getLogger(__name__)


@pytest.fixture
def clear_sys_argv():
    """
    Fixture to clear sys.argv before each test.
    """
    original_argv = sys.argv.copy()
    sys.argv = [original_argv[0]]  # Reset to script name only
    yield
    sys.argv = original_argv  # Restore original argv after test


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_dry_run() -> None:
    """
    Test that the --dry-run flag is correctly parsed when present.
    """
    test_path = "some/path"
    # Simulate command-line arguments: script.py some/path --dry-run
    sys.argv = ["script.py", test_path, "--dry-run"]

    args = get_user_arguments()

    assert args.dry_run is True, "dry_run should be True when --dry-run flag is present"
    assert args.path == test_path, f"Path should be '{test_path}'"
    assert args.auto_rename is False, "auto_rename should be False by default"


def test_get_user_arguments_without_dry_run() -> None:
    """
    Test that the --dry-run flag is correctly parsed when absent.
    """
    test_path = "some/path"
    # Simulate command-line arguments: script.py some/path
    sys.argv = ["script.py", test_path]

    args = get_user_arguments()

    assert (
        args.dry_run is False
    ), "dry_run should be False when --dry-run flag is absent"
    assert args.path == test_path, f"Path should be '{test_path}'"
    assert args.auto_rename is False, "auto_rename should be False by default"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_all_flags() -> None:
    """
    Test that all flags (--dry-run and --auto-rename) are correctly parsed together.
    """
    test_path = "another/path"
    # Simulate command-line arguments: script.py another/path --dry-run --auto-rename
    sys.argv = ["script.py", test_path, "--dry-run", "--auto-rename"]

    args = get_user_arguments()

    assert args.dry_run is True, "dry_run should be True when --dry-run flag is present"
    assert (
        args.auto_rename is True
    ), "auto_rename should be True when --auto-rename flag is present"
    assert args.path == test_path, f"Path should be '{test_path}'"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_auto_rename_only() -> None:
    """
    Test that the --auto-rename flag is correctly parsed when present without --dry-run.
    """
    test_path = "path/without/dryrun"
    # Simulate command-line arguments: script.py path/without/dryrun --auto-rename
    sys.argv = ["script.py", test_path, "--auto-rename"]

    args = get_user_arguments()

    assert (
        args.dry_run is False
    ), "dry_run should be False when --dry-run flag is absent"
    assert (
        args.auto_rename is True
    ), "auto_rename should be True when --auto-rename flag is present"
    assert args.path == test_path, f"Path should be '{test_path}'"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_missing_path() -> None:
    """
    Test that the parser raises an error when the mandatory 'path' argument is missing.
    """
    # Simulate command-line arguments: script.py --dry-run
    sys.argv = ["script.py", "--dry-run"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert (
        exc_info.value.code == 2
    ), "Parser should exit with code 2 for argument parsing errors"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_invalid_flag() -> None:
    """
    Test that the parser raises an error when an invalid flag is provided.
    """
    test_path = "some/path"
    # Simulate command-line arguments: script.py some/path --invalid-flag
    sys.argv = ["script.py", test_path, "--invalid-flag"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert (
        exc_info.value.code == 2
    ), "Parser should exit with code 2 for unrecognized arguments"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_path_with_spaces() -> None:
    """
    Test that the parser correctly handles paths with spaces.
    """
    test_path = "path/with spaces/in/name"
    # Simulate command-line arguments: script.py "path/with spaces/in/name" --dry-run
    sys.argv = ["script.py", test_path, "--dry-run"]

    args = get_user_arguments()

    assert args.dry_run is True, "dry_run should be True when --dry-run flag is present"
    assert args.path == test_path, f"Path should be '{test_path}'"
    assert args.auto_rename is False, "auto_rename should be False by default"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_multiple_paths() -> None:
    """
    Test that the parser correctly handles multiple paths by only accepting the first one.
    (Assuming the parser is designed to accept only one path)
    """
    test_path = "first/path"
    second_path = "second/path"
    # Simulate command-line arguments: script.py first/path second/path --dry-run
    sys.argv = ["script.py", test_path, second_path, "--dry-run"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert (
        exc_info.value.code == 2
    ), "Parser should exit with code 2 when extra positional arguments are provided"


def test_is_supported_filetype() -> None:
    """
    Test if the file type is supported.
    """
    temp_txt_file_path = None
    temp_unsupported_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".txt", mode="w", encoding="utf-8"
        ) as temp_txt_file:
            temp_txt_file.write("This is a sample text.")
            temp_txt_file_path = temp_txt_file.name

        # Test if the text file is supported
        assert is_supported_filetype(temp_txt_file_path) is True

        # Test if an unsupported file type returns False
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".unsupported", mode="w", encoding="utf-8"
        ) as temp_unsupported_file:
            temp_unsupported_file.write("This is an unsupported file type.")
            temp_unsupported_file_path = temp_unsupported_file.name
            assert is_supported_filetype(temp_unsupported_file_path) is False
    finally:
        # Clean up the temporary files
        for file_path in (temp_txt_file_path, temp_unsupported_file_path):
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    logger.warning(
                        "Failed to remove temporary file %s: %s", file_path, str(e)
                    )


def test_calculate_md5():
    """
    Test that calculate_md5 correctly computes the MD5 hash of a file.
    """
    temp_file_path = None
    try:
        # Create a temporary file with known content
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_file:
            temp_file.write("Test content for MD5.")
            temp_file_path = temp_file.name

        # Expected MD5 hash for "Test content for MD5."
        expected_md5 = hashlib.md5(b"Test content for MD5.").hexdigest()

        # Calculate MD5 using the function
        calculated_md5 = calculate_md5(temp_file_path)

        assert (
            calculated_md5 == expected_md5
        ), f"Expected MD5: {expected_md5}, but got: {calculated_md5}"
    finally:
        # Clean up the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def test_calculate_md5_file_not_found():
    """
    Test that calculate_md5 returns None when the file does not exist.
    """
    non_existent_file = "non_existent_file.txt"
    assert (
        calculate_md5(non_existent_file) is None
    ), "calculate_md5 should return None for non-existent files"


@mock.patch("sqlite3.connect")
def test_connect_to_db(mock_connect):
    """
    Test that connect_to_db calls sqlite3.connect with the correct DB_FILE.
    """
    connect_to_db()
    mock_connect.assert_called_once_with(DB_FILE)


@mock.patch("src.ai_file_classifier.utils.connect_to_db")
def test_insert_or_update_file(mock_connect):
    """
    Test that insert_or_update_file correctly inserts or updates a file record.
    """
    mock_conn = mock.MagicMock()
    mock_connect.return_value = mock_conn

    file_path = "/path/to/file.txt"
    suggested_name = "new_file_name"
    metadata = {
        "category": "Category1",
        "description": "A sample file.",
        "vendor": "VendorX",
        "date": "2023-10-01",
    }

    insert_or_update_file(file_path, suggested_name, metadata)

    mock_connect.assert_called_once()
    mock_conn.cursor.assert_called_once()
    mock_conn.cursor.return_value.execute.assert_called_once_with(
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


@mock.patch("src.ai_file_classifier.utils.connect_to_db")
def test_insert_or_update_file_db_error(mock_connect):
    """
    Test that insert_or_update_file handles SQLite errors gracefully.
    """
    mock_connect.side_effect = sqlite3.Error("DB connection failed")

    file_path = "/path/to/file.txt"
    suggested_name = "new_file_name"
    metadata = {
        "category": "Category1",
        "description": "A sample file.",
        "vendor": "VendorX",
        "date": "2023-10-01",
    }

    with pytest.raises(sqlite3.Error):
        insert_or_update_file(file_path, suggested_name, metadata)


@mock.patch("src.ai_file_classifier.utils.connect_to_db")
def test_get_all_suggested_changes(mock_connect):
    """
    Test that get_all_suggested_changes retrieves the correct data from the database.
    """
    mock_conn = mock.MagicMock()
    mock_cursor = mock.MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        ("/path/to/file1.txt", "new_file1"),
        ("/path/to/file2.pdf", "new_file2"),
    ]

    changes = get_all_suggested_changes()

    mock_connect.assert_called_once()
    mock_conn.cursor.assert_called_once()
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


@mock.patch("src.ai_file_classifier.utils.connect_to_db")
def test_get_all_suggested_changes_db_error(mock_connect):
    """
    Test that get_all_suggested_changes handles SQLite errors gracefully.
    """
    mock_connect.side_effect = sqlite3.Error("DB connection failed")

    changes = get_all_suggested_changes()

    assert changes == []


@mock.patch("os.rename")
@mock.patch("src.ai_file_classifier.utils.logger")
def test_rename_files_success(mock_logger, mock_rename):
    """
    Test that rename_files successfully renames files as per suggested changes.
    """
    suggested_changes = [
        {"file_path": "/path/to/file1.txt", "suggested_name": "new_file1"},
        {"file_path": "/path/to/file2.pdf", "suggested_name": "new_file2"},
    ]

    rename_files(suggested_changes)

    expected_calls = [
        mock.call("/path/to/file1.txt", "/path/to/new_file1.txt"),
        mock.call("/path/to/file2.pdf", "/path/to/new_file2.pdf"),
    ]
    mock_rename.assert_has_calls(expected_calls, any_order=False)
    assert mock_logger.info.call_count == 2
    mock_logger.info.assert_any_call(
        "File '/path/to/file1.txt' renamed to '/path/to/new_file1.txt'."
    )
    mock_logger.info.assert_any_call(
        "File '/path/to/file2.pdf' renamed to '/path/to/new_file2.pdf'."
    )


@mock.patch("os.rename", side_effect=OSError("Rename failed"))
@mock.patch("src.ai_file_classifier.utils.logger")
def test_rename_files_rename_error(mock_logger, mock_rename):
    """
    Test that rename_files handles rename errors gracefully.
    """
    suggested_changes = [
        {"file_path": "/path/to/file1.txt", "suggested_name": "new_file1"},
    ]

    with pytest.raises(OSError, match="Rename failed"):
        rename_files(suggested_changes)

    mock_rename.assert_called_once_with("/path/to/file1.txt", "/path/to/new_file1.txt")
    mock_logger.error.assert_called_once_with(
        f"Error renaming file '/path/to/file1.txt' to 'new_file1': Rename failed",
        exc_info=True,
    )


@mock.patch("src.ai_file_classifier.utils.insert_or_update_file")
@mock.patch("src.ai_file_classifier.utils.is_supported_filetype", return_value=True)
@mock.patch("src.ai_file_classifier.utils.os.path.exists", return_value=True)
@mock.patch("src.ai_file_classifier.utils.os.path.isfile", return_value=True)
@mock.patch("src.ai_file_classifier.utils.analyze_file_content")
@mock.patch("src.ai_file_classifier.utils.logger")
def test_process_file_success(
    mock_logger,
    mock_analyze,
    mock_isfile,
    mock_exists,
    mock_supported,
    mock_insert_update,
):
    """
    Test that process_file successfully processes a supported file.
    """
    file_path = "/path/to/file.txt"
    model = "model_v1"
    client = mock.MagicMock()

    mock_analyze.return_value = (
        "suggested_name",
        "Category1",
        "VendorX",
        "Description",
        "2023-10-01",
    )

    process_file(file_path, model, client)

    mock_exists.assert_called_once_with(file_path)
    mock_isfile.assert_called_once_with(file_path)
    mock_supported.assert_called_once_with(file_path)
    mock_analyze.assert_called_once_with(file_path, model, client)
    mock_insert_update.assert_called_once_with(
        file_path,
        "suggested_name",
        {
            "category": "Category1",
            "description": "Description",
            "vendor": "VendorX",
            "date": "2023-10-01",
        },
    )
    mock_logger.info.assert_called_once_with(
        "Suggested name for the file: suggested_name"
    )


@mock.patch("src.ai_file_classifier.utils.logger")
def test_process_file_file_not_exists(mock_logger):
    """
    Test that process_file logs an error when the file does not exist.
    """
    file_path = "/path/to/non_existent_file.txt"
    model = "model_v1"
    client = mock.MagicMock()

    with mock.patch("src.ai_file_classifier.utils.os.path.exists", return_value=False):
        process_file(file_path, model, client)

    mock_logger.error.assert_called_once_with(f"The file '{file_path}' does not exist.")


@mock.patch("src.ai_file_classifier.utils.logger")
def test_process_file_not_a_file(mock_logger):
    """
    Test that process_file logs an error when the path is not a file.
    """
    file_path = "/path/to/directory"
    model = "model_v1"
    client = mock.MagicMock()

    with mock.patch(
        "src.ai_file_classifier.utils.os.path.exists", return_value=True
    ), mock.patch("src.ai_file_classifier.utils.os.path.isfile", return_value=False):
        process_file(file_path, model, client)

    mock_logger.error.assert_called_once_with(f"The path '{file_path}' is not a file.")


@mock.patch("src.ai_file_classifier.utils.logger")
def test_process_file_unsupported_filetype(mock_logger):
    """
    Test that process_file logs an error when the file type is unsupported.
    """
    file_path = "/path/to/file.unsupported"
    model = "model_v1"
    client = mock.MagicMock()

    with mock.patch(
        "src.ai_file_classifier.utils.os.path.exists", return_value=True
    ), mock.patch(
        "src.ai_file_classifier.utils.os.path.isfile", return_value=True
    ), mock.patch(
        "src.ai_file_classifier.utils.is_supported_filetype", return_value=False
    ):
        process_file(file_path, model, client)

    mock_logger.error.assert_called_once_with(
        f"The file '{file_path}' is not a supported file type."
    )


@mock.patch(
    "src.ai_file_classifier.utils.analyze_file_content",
    side_effect=RuntimeError("Analysis failed"),
)
@mock.patch("src.ai_file_classifier.utils.logger")
@mock.patch("src.ai_file_classifier.utils.is_supported_filetype", return_value=True)
@mock.patch("src.ai_file_classifier.utils.os.path.exists", return_value=True)
@mock.patch("src.ai_file_classifier.utils.os.path.isfile", return_value=True)
def test_process_file_analysis_failure(
    mock_isfile, mock_exists, mock_supported, mock_logger, mock_analyze
):
    """
    Test that process_file logs an error when analyze_file_content raises an exception.
    """
    file_path = "/path/to/file.txt"
    model = "model_v1"
    client = mock.MagicMock()

    # Expect a RuntimeError to be raised
    with pytest.raises(RuntimeError, match="Analysis failed"):
        process_file(file_path, model, client)

    mock_analyze.assert_called_once_with(file_path, model, client)
    mock_logger.error.assert_called_once_with("Analysis failed")
