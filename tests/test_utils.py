"""Unit tests for the utils module."""

import logging
import os
import tempfile

import pytest

from src.ai_file_classifier.utils import is_supported_filetype

logger = logging.getLogger(__name__)


def test_is_supported_filetype():
    """
    Test if the file type is supported.
    """
    temp_txt_file_path = None
    temp_unsupported_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w',
                                         encoding='utf-8') as temp_txt_file:
            temp_txt_file.write("This is a sample text.")
            temp_txt_file_path = temp_txt_file.name

        # Test if the text file is supported
        assert is_supported_filetype(temp_txt_file_path) is True

        # Test if an unsupported file type returns False
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".unsupported",
            mode='w',
            encoding='utf-8'
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
                        "Failed to remove temporary file %s: %s",
                        file_path,
                        str(e)
                    )


if __name__ == "__main__":
    pytest.main()
