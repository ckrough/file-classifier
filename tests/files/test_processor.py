"""Unit tests for file processor."""

from unittest import mock

import pytest

from src.files.processor import process_file, ProcessingOptions


@pytest.mark.unit
@mock.patch("src.files.processor.logger")
def test_process_file_file_not_exists(mock_logger):
    """Test that process_file logs an error when the file does not exist."""
    file_path = "/path/to/non_existent_file.txt"
    client = mock.MagicMock()

    with mock.patch("src.files.processor.os.path.exists", return_value=False):
        result = process_file(file_path, client)

    assert result is None
    assert mock_logger.error.called
    call_msg = str(mock_logger.error.call_args)
    assert "does not exist" in call_msg.lower() or "not found" in call_msg.lower()


@pytest.mark.unit
@mock.patch("src.files.processor.logger")
def test_process_file_not_a_file(mock_logger):
    """Test that process_file logs an error when the path is not a file."""
    file_path = "/path/to/directory"
    client = mock.MagicMock()

    with (
        mock.patch("src.files.processor.os.path.exists", return_value=True),
        mock.patch("src.files.processor.os.path.isfile", return_value=False),
    ):
        result = process_file(file_path, client)

    assert result is None
    assert mock_logger.error.called
    call_msg = str(mock_logger.error.call_args)
    assert "not a file" in call_msg.lower()


@pytest.mark.unit
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
        result = process_file(file_path, client)

    assert result is None
    assert mock_logger.error.called
    call_msg = str(mock_logger.error.call_args)
    assert "supported" in call_msg.lower()


@pytest.mark.unit
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
    """Test that process_file logs an error when
    analyze_file_content raises an exception."""
    file_path = "/path/to/file.txt"
    client = mock.MagicMock()

    # Expect a RuntimeError to be raised
    options = ProcessingOptions(validate_type=False)
    with pytest.raises(RuntimeError, match="Analysis failed"):
        process_file(file_path, client, options)

    mock_analyze.assert_called_once_with(file_path, client, None)
    assert mock_logger.error.called
    call_msg = str(mock_logger.error.call_args)
    assert "failed" in call_msg.lower()
