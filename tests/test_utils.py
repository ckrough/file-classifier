"""Unit tests for the utils module."""

import logging
import os
import sys
import tempfile

import pytest

from src.ai_file_classifier.utils import get_user_arguments, is_supported_filetype

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
