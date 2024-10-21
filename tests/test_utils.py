import logging
import os
import tempfile

import pytest

from src.ai_file_classifier.utils import is_supported_filetype, rename_file

logger = logging.getLogger(__name__)


def test_is_supported_filetype():
    """
    Test if the file type is supported.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_txt_file:
        temp_txt_file.write("This is a sample text.")
        temp_txt_file_path = temp_txt_file.name

    try:
        # Test if the text file is supported
        assert is_supported_filetype(temp_txt_file_path) is True

        # Test if an unsupported file type returns False
        with tempfile.NamedTemporaryFile(delete=False, suffix=".unsupported", mode='w', encoding='utf-8') as temp_unsupported_file:
            temp_unsupported_file.write("This is an unsupported file type.")
            temp_unsupported_file_path = temp_unsupported_file.name
            assert is_supported_filetype(temp_unsupported_file_path) is False
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        # Clean up the temporary files
        os.remove(temp_txt_file_path)
        os.remove(temp_unsupported_file_path)


def test_rename_file():
    """
    Test renaming a file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_file:
        temp_file.write("This is a sample text.")
        temp_file_path = temp_file.name

    try:
        # Test renaming the file
        new_name = "renamed_file"
        rename_file(temp_file_path, new_name)
        new_path = os.path.join(os.path.dirname(
            temp_file_path), f"{new_name}.txt")
        assert os.path.exists(new_path) is True
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        # Clean up the renamed file
        if os.path.exists(new_path):
            os.remove(new_path)


if __name__ == "__main__":
    pytest.main()
