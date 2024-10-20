import os
import tempfile

import pytest

from src.ai_file_classifier.prompt_loader import load_and_format_prompt


def test_load_and_format_prompt():
    """
    Test loading and formatting a prompt from a file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_prompt_file:
        temp_prompt_file.write("Hello, {name}! Welcome to the test.")
        temp_prompt_file_path = temp_prompt_file.name

    try:
        # Test the function
        formatted_prompt = load_and_format_prompt(
            temp_prompt_file_path, name="Tester")
        assert formatted_prompt == "Hello, Tester! Welcome to the test."
    finally:
        # Clean up the temporary file
        os.remove(temp_prompt_file_path)


if __name__ == "__main__":
    pytest.main()
