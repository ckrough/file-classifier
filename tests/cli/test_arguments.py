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


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_basic_path() -> None:
    """Test that basic path argument is correctly parsed."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path]

    args = get_user_arguments()

    assert args.path == test_path, f"Path should be '{test_path}'"
    assert args.batch is False, "batch should be False by default"
    assert args.format == "json", "format should default to 'json'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_with_batch() -> None:
    """Test that the --batch flag is correctly parsed when present."""
    sys.argv = ["script.py", "--batch"]

    args = get_user_arguments()

    assert args.batch is True, "batch should be True when --batch flag is present"
    assert args.path is None, "path should be None in batch mode"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_format_json() -> None:
    """Test that --format=json is correctly parsed."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--format", "json"]

    args = get_user_arguments()

    assert args.format == "json", "format should be 'json'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_format_csv() -> None:
    """Test that --format=csv is correctly parsed."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--format", "csv"]

    args = get_user_arguments()

    assert args.format == "csv", "format should be 'csv'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_format_tsv() -> None:
    """Test that --format=tsv is correctly parsed."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--format", "tsv"]

    args = get_user_arguments()

    assert args.format == "tsv", "format should be 'tsv'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_batch_with_format() -> None:
    """Test that --batch and --format can be combined."""
    sys.argv = ["script.py", "--batch", "--format", "csv"]

    args = get_user_arguments()

    assert args.batch is True, "batch should be True"
    assert args.format == "csv", "format should be 'csv'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_missing_path_without_batch() -> None:
    """Test that missing path without --batch raises SystemExit."""
    sys.argv = ["script.py"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert exc_info.value.code == 2, "SystemExit code should be 2 for missing argument"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_path_and_batch_conflict() -> None:
    """Test that providing both path and --batch raises SystemExit."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--batch"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert (
        exc_info.value.code == 2
    ), "SystemExit code should be 2 for conflicting arguments"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_invalid_flag() -> None:
    """Test that an invalid flag raises SystemExit."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--invalid-flag"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert exc_info.value.code == 2, "SystemExit code should be 2 for invalid flag"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_invalid_format() -> None:
    """Test that an invalid format value raises SystemExit."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--format", "xml"]

    with pytest.raises(SystemExit) as exc_info:
        get_user_arguments()

    assert exc_info.value.code == 2, "SystemExit code should be 2 for invalid format"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_path_with_spaces() -> None:
    """Test that paths containing spaces are handled correctly."""
    test_path = "path with spaces/file"
    sys.argv = ["script.py", test_path]

    args = get_user_arguments()

    assert args.path == test_path, f"Path should be '{test_path}'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_verbosity_quiet() -> None:
    """Test that --quiet flag sets verbosity correctly."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--quiet"]

    args = get_user_arguments()

    assert args.verbosity == "quiet", "verbosity should be 'quiet'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_verbosity_verbose() -> None:
    """Test that --verbose flag sets verbosity correctly."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--verbose"]

    args = get_user_arguments()

    assert args.verbosity == "verbose", "verbosity should be 'verbose'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_verbosity_debug() -> None:
    """Test that --debug flag sets verbosity correctly."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--debug"]

    args = get_user_arguments()

    assert args.verbosity == "debug", "verbosity should be 'debug'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_verbosity_default() -> None:
    """Test that verbosity defaults to 'normal'."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path]

    args = get_user_arguments()

    assert args.verbosity == "normal", "verbosity should default to 'normal'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_extraction_strategy() -> None:
    """Test that --extraction-strategy flag is correctly parsed."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--extraction-strategy", "full"]

    args = get_user_arguments()

    assert args.extraction_strategy == "full", "extraction_strategy should be 'full'"


@pytest.mark.unit
@pytest.mark.usefixtures("clear_sys_argv")
def test_get_user_arguments_full_extraction() -> None:
    """Test that --full-extraction flag overrides extraction_strategy to 'full'."""
    test_path = "some/path"
    sys.argv = ["script.py", test_path, "--full-extraction"]

    args = get_user_arguments()

    assert (
        args.extraction_strategy == "full"
    ), "extraction_strategy should be 'full' when --full-extraction is set"
