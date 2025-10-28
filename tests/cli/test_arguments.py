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
    assert args.destination is None, "destination should be None by default"
    assert args.move is False, "move should be False by default"


def test_get_user_arguments_without_dry_run() -> None:
    """Test that the --dry-run flag is correctly parsed when absent."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path]

    args = get_user_arguments()

    assert (
        args.dry_run is False
    ), "dry_run should be False when --dry-run flag is absent"
    assert args.path == test_path, f"Path should be '{test_path}'"
    assert args.destination is None, "destination should be None by default"
    assert args.move is False, "move should be False by default"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_destination_and_move() -> None:
    """Test that --destination and --move flags are correctly parsed together."""
    test_path = "another/path"
    test_dest = "/archive/root"
    sys.argv = ["script.py", test_path, "--destination", test_dest, "--move"]

    args = get_user_arguments()

    assert args.destination == test_dest, f"destination should be '{test_dest}'"
    assert args.move is True, "move should be True when --move flag is present"
    assert args.path == test_path, f"Path should be '{test_path}'"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_destination_only() -> None:
    """Test that --destination without --move is accepted (but move is disabled)."""
    test_path = "path/to/file"
    test_dest = "/archive/root"
    sys.argv = ["script.py", test_path, "--destination", test_dest]

    args = get_user_arguments()

    assert args.destination == test_dest, f"destination should be '{test_dest}'"
    assert args.move is False, "move should be False when --move flag is absent"
    assert args.path == test_path, f"Path should be '{test_path}'"


@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_move_without_destination_fails() -> None:
    """Test that --move without --destination raises SystemExit."""
    test_path = "path/to/file"
    sys.argv = ["script.py", test_path, "--move"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert exc_info.value.code == 2, "SystemExit code should be 2 for validation error"


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
