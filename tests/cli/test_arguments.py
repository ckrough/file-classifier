"""Unit tests for CLI argument parsing."""

import sys

import pytest

from src.cli.arguments import parse_arguments as get_user_arguments


@pytest.fixture
def clear_sys_argv():
    """Fixture to clear sys.argv before each test."""
    original_argv = sys.argv.copy()
    sys.argv = [original_argv[0]]  # Reset to script name only
    yield
    sys.argv = original_argv  # Restore original argv after test


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_dry_run() -> None:
    """Test that the --dry-run flag is correctly parsed when present."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--dry-run"]

    args = get_user_arguments()

    assert args.dry_run is True, "dry_run should be True when --dry-run flag is present"
    assert args.path == test_path, f"Path should be '{test_path}'"
    assert args.auto_rename is False, "auto_rename should be False by default"


def test_get_user_arguments_without_dry_run() -> None:
    """Test that the --dry-run flag is correctly parsed when absent."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path]

    args = get_user_arguments()

    assert (
        args.dry_run is False
    ), "dry_run should be False when --dry-run flag is absent"
    assert args.path == test_path, f"Path should be '{test_path}'"
    assert args.auto_rename is False, "auto_rename should be False by default"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_all_flags() -> None:
    """Test that all flags (--dry-run and --auto-rename) are correctly parsed
    together."""
    test_path = "another/path"
    sys.argv = ["script.py", test_path, "--dry-run", "--auto-rename"]

    args = get_user_arguments()

    assert args.dry_run is True, "dry_run should be True when --dry-run flag is present"
    assert (
        args.auto_rename is True
    ), "auto_rename should be True when --auto-rename flag is present"
    assert args.path == test_path, f"Path should be '{test_path}'"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_auto_rename_only() -> None:
    """Test that the --auto-rename flag is correctly parsed when present
    without --dry-run."""
    test_path = "path/without/dryrun"
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
    """Test that missing required 'path' argument raises SystemExit."""
    sys.argv = ["script.py"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert exc_info.value.code == 2, "SystemExit code should be 2 for missing argument"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_invalid_flag() -> None:
    """Test that an invalid flag raises SystemExit."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--invalid-flag"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert exc_info.value.code == 2, "SystemExit code should be 2 for invalid flag"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_path_with_spaces() -> None:
    """Test that paths containing spaces are handled correctly."""
    test_path = "path with spaces/file"
    sys.argv = ["script.py", test_path]

    args = get_user_arguments()

    assert args.path == test_path, f"Path should be '{test_path}'"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_multiple_paths() -> None:
    """Test that only the first positional argument is accepted as the path."""
    test_path = "first/path"
    sys.argv = ["script.py", test_path, "second/path"]

    with pytest.raises(SystemExit):
        get_user_arguments()
