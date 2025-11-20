"""Unit tests for file operations."""

import pytest

from src.files.operations import is_supported_filetype


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
