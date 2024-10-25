"""
This module contains unit tests for the prompt_loader module.
"""

import logging
import os
import tempfile

import pytest

from src.ai_file_classifier.prompt_loader import load_and_format_prompt

logger = logging.getLogger(__name__)


def test_load_and_format_prompt():
    """
    Test the loading and formatting of a prompt from a file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w',
                                     encoding='utf-8') as temp_prompt_file:
        temp_prompt_file.write("Hello, {name}! This is a test prompt.")
        temp_prompt_file_path = temp_prompt_file.name

    try:
        # Test loading and formatting with valid keyword arguments
        result = load_and_format_prompt(temp_prompt_file_path, name="Alice")
        assert result == "Hello, Alice! This is a test prompt."

        # Test loading and formatting with missing keyword arguments
        result = load_and_format_prompt(temp_prompt_file_path)
        assert result == ""
    except FileNotFoundError:
        logger.error("Test failed: Prompt file not found.")
    except PermissionError:
        logger.error("Test failed: Permission denied accessing prompt file.")
    except KeyError as e:
        logger.error("Test failed: Missing key in prompt format string: %s", e)
    finally:
        # Clean up the temporary file
        try:
            os.remove(temp_prompt_file_path)
        except OSError as e:
            logger.warning("Failed to remove temporary file: %s", e)


if __name__ == "__main__":
    pytest.main()
