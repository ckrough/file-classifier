"""Unit tests for file operations."""

from unittest import mock

import pytest

from src.files.operations import is_supported_filetype, rename_files


@pytest.mark.unit
def test_is_supported_filetype(tmp_path):
    """Test if the file type is supported."""
    # Create a supported text file.
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("This is a sample text.", encoding="utf-8")
    assert is_supported_filetype(str(txt_file)) is True

    # Create an unsupported file with binary content.
    bin_file = tmp_path / "file.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03\x04")
    assert is_supported_filetype(str(bin_file)) is False


@pytest.mark.unit
@mock.patch("os.rename")
@mock.patch("src.files.operations.logger")
def test_rename_files_success(mock_logger, mock_rename):
    """Test that rename_files successfully renames files as per suggested changes."""
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


@pytest.mark.unit
@mock.patch("os.rename", side_effect=OSError("Rename failed"))
@mock.patch("src.files.operations.logger")
def test_rename_files_rename_error(mock_logger, mock_rename):
    """Test that rename_files handles rename errors gracefully."""
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


@pytest.mark.integration
def test_rename_files_preserves_extension_integration(tmp_path):
    """Integration test: Test that rename_files preserves file extensions."""
    # Create a temporary file with an extension
    original_file = tmp_path / "original_file.txt"
    original_file.write_text("test content")

    suggested_changes = [
        {
            "file_path": str(original_file),
            "suggested_name": "renamed_file",  # No extension
        }
    ]

    # Call the actual rename_files function
    rename_files(suggested_changes)

    # Check that the renamed file exists with the preserved extension
    renamed_file = tmp_path / "renamed_file.txt"
    assert renamed_file.exists(), "Renamed file should exist with preserved extension"
    assert not original_file.exists(), "Original file should no longer exist"
    assert (
        renamed_file.read_text() == "test content"
    ), "File content should remain unchanged"


@pytest.mark.integration
def test_rename_files_uppercase_extension(tmp_path):
    """Test that rename_files preserves uppercase extensions (e.g., .PDF)."""
    original_file = tmp_path / "document.PDF"
    original_file.write_text("pdf content")

    suggested_changes = [
        {"file_path": str(original_file), "suggested_name": "new_document"}
    ]

    rename_files(suggested_changes)

    renamed_file = tmp_path / "new_document.PDF"
    assert renamed_file.exists(), "File with uppercase extension should be renamed"
    assert (
        renamed_file.read_text() == "pdf content"
    ), "File content should remain unchanged"


@pytest.mark.integration
def test_rename_files_multiple_dots_in_filename(tmp_path):
    """Test that rename_files correctly handles filenames with multiple dots."""
    original_file = tmp_path / "archive.backup.tar.gz"
    original_file.write_text("compressed content")

    suggested_changes = [
        {"file_path": str(original_file), "suggested_name": "new_archive"}
    ]

    rename_files(suggested_changes)

    # Only the last extension (.gz) should be preserved
    renamed_file = tmp_path / "new_archive.gz"
    assert (
        renamed_file.exists()
    ), "File with compound extension should preserve only last extension"
    assert (
        renamed_file.read_text() == "compressed content"
    ), "File content should remain unchanged"
