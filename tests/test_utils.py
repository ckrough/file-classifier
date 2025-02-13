"""Unit tests for the utils module."""

import hashlib
import logging
import sys
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


def test_is_supported_filetype(tmp_path):
    """
    Test if the file type is supported.
    """
    # Create a supported text file.
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("This is a sample text.", encoding="utf-8")
    assert is_supported_filetype(str(txt_file)) is True

    # Create an unsupported file with binary content.
    bin_file = tmp_path / "file.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03\x04")
    assert is_supported_filetype(str(bin_file)) is False


def test_calculate_md5(tmp_path):
    """
    Test that calculate_md5 correctly computes the MD5 hash of a file.
    """
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Test content for MD5.", encoding="utf-8")
    expected_md5 = hashlib.md5("Test content for MD5.".encode("utf-8")).hexdigest()
    calculated_md5 = calculate_md5(str(test_file))
    assert (
        calculated_md5 == expected_md5
    ), f"Expected MD5: {expected_md5}, but got: {calculated_md5}"


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
        "File '%s' renamed to '%s'.", "/path/to/file1.txt", "/path/to/new_file1.txt"
    )
    mock_logger.info.assert_any_call(
        "File '%s' renamed to '%s'.", "/path/to/file2.pdf", "/path/to/new_file2.pdf"
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
        "Error renaming file '%s' to '%s': %s",
        "/path/to/file1.txt",
        "new_file1",
        "Rename failed",
        exc_info=True,
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

    mock_logger.error.assert_called_once_with(
        "The file '%s' does not exist.", "/path/to/non_existent_file.txt"
    )


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

    mock_logger.error.assert_called_once_with(
        "The path '%s' is not a file.", "/path/to/directory"
    )


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
        "The file '%s' is not a supported file type.", "/path/to/file.unsupported"
    )


@mock.patch(
    "src.ai_file_classifier.utils.analyze_file_content",
    side_effect=RuntimeError("Analysis failed"),
)
@mock.patch("src.ai_file_classifier.utils.is_supported_filetype", return_value=True)
@mock.patch("src.ai_file_classifier.utils.os.path.isfile", return_value=True)
@mock.patch("src.ai_file_classifier.utils.os.path.exists", return_value=True)
@mock.patch("src.ai_file_classifier.utils.logger")
def test_process_file_analysis_failure(
    mock_logger, _mock_exists, _mock_isfile, _mock_supported, mock_analyze
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
