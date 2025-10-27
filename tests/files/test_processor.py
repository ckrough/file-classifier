"""Unit tests for file processor."""

from unittest import mock

import pytest

from src.files.processor import process_file


@mock.patch("src.files.processor.logger")
def test_process_file_file_not_exists(mock_logger):
    """Test that process_file logs an error when the file does not exist."""
    file_path = "/path/to/non_existent_file.txt"
    client = mock.MagicMock()

    with mock.patch("src.files.processor.os.path.exists", return_value=False):
        process_file(file_path, client)

    mock_logger.error.assert_called_once_with(
        "The file '%s' does not exist.", "/path/to/non_existent_file.txt"
    )


@mock.patch("src.files.processor.logger")
def test_process_file_not_a_file(mock_logger):
    """Test that process_file logs an error when the path is not a file."""
    file_path = "/path/to/directory"
    client = mock.MagicMock()

    with (
        mock.patch("src.files.processor.os.path.exists", return_value=True),
        mock.patch("src.files.processor.os.path.isfile", return_value=False),
    ):
        process_file(file_path, client)

    mock_logger.error.assert_called_once_with(
        "The path '%s' is not a file.", "/path/to/directory"
    )


@mock.patch("src.files.processor.logger")
def test_process_file_unsupported_filetype(mock_logger):
    """Test that process_file logs an error when the file type is unsupported."""
    file_path = "/path/to/file.unsupported"
    client = mock.MagicMock()

    with (
        mock.patch("src.files.processor.os.path.exists", return_value=True),
        mock.patch("src.files.processor.os.path.isfile", return_value=True),
        mock.patch("src.files.processor.is_supported_filetype", return_value=False),
    ):
        process_file(file_path, client)

    mock_logger.error.assert_called_once_with(
        "The file '%s' is not a supported file type.", "/path/to/file.unsupported"
    )


@mock.patch(
    "src.files.processor.analyze_file_content",
    side_effect=RuntimeError("Analysis failed"),
)
@mock.patch("src.files.processor.is_supported_filetype", return_value=True)
@mock.patch("src.files.processor.os.path.isfile", return_value=True)
@mock.patch("src.files.processor.os.path.exists", return_value=True)
@mock.patch("src.files.processor.logger")
def test_process_file_analysis_failure(
    mock_logger, _mock_exists, _mock_isfile, _mock_supported, mock_analyze
):
    """Test that process_file logs an error when analyze_file_content raises an exception."""
    file_path = "/path/to/file.txt"
    client = mock.MagicMock()

    # Expect a RuntimeError to be raised
    with pytest.raises(RuntimeError, match="Analysis failed"):
        process_file(file_path, client)

    mock_analyze.assert_called_once_with(file_path, client)
    mock_logger.error.assert_called_once_with("Analysis failed")
