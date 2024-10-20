import os
import tempfile

import pytest

from src.ai_file_classifier.utils import is_supported_filetype, rename_file


def test_is_supported_filetype():
    """
    Test if the specified file is a supported type.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_txt_file:
        temp_txt_file.write("This is a test text file.")
        temp_txt_file_path = temp_txt_file.name

    try:
        # Test with a supported file type (.txt)
        assert is_supported_filetype(temp_txt_file_path) is True
    finally:
        # Clean up the temporary file
        os.remove(temp_txt_file_path)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".unsupported") as temp_unsupported_file:
        temp_unsupported_file_path = temp_unsupported_file.name

    try:
        # Test with an unsupported file type (empty file with unknown extension)
        assert is_supported_filetype(temp_unsupported_file_path) is False
    finally:
        # Clean up the temporary file
        os.remove(temp_unsupported_file_path)


def test_rename_file():
    """
    Test renaming a file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_txt_file:
        temp_txt_file.write("This is a test text file.")
        temp_txt_file_path = temp_txt_file.name

    new_name = "renamed_test_file"
    try:
        # Test the function
        rename_file(temp_txt_file_path, new_name)
        new_file_path = os.path.join(os.path.dirname(temp_txt_file_path), new_name + ".txt")
        assert os.path.exists(new_file_path)
    finally:
        # Clean up the temporary file
        if os.path.exists(new_file_path):
            os.remove(new_file_path)


if __name__ == "__main__":
    pytest.main()
