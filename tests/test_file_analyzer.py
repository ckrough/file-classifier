import os
import tempfile

import pytest

from src.ai_file_classifier.file_analyzer import analyze_file_content


def test_analyze_file_content():
    """
    Test the analysis of file content to determine a suggested name.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_txt_file:
        temp_txt_file.write("This is a sample text for analysis.")
        temp_txt_file_path = temp_txt_file.name

    try:
        # Test with the sample text file
        suggested_name = analyze_file_content(temp_txt_file_path)
        assert suggested_name is not None
        assert isinstance(suggested_name, str)
    finally:
        # Clean up the temporary file
        os.remove(temp_txt_file_path)


if __name__ == "__main__":
    pytest.main()
