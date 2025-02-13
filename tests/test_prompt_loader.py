"""
This module contains unit tests for the prompt_loader module.
"""

from pathlib import Path
from src.ai_file_classifier.prompt_loader import load_and_format_prompt


def test_load_prompt_valid(tmp_path):
    """Test loading and formatting a prompt with valid arguments."""
    # Create a temporary prompt file with proper formatting.
    prompt_file: Path = tmp_path / "prompt.txt"
    prompt_file.write_text("Hello, {name}! This is a test prompt.", encoding="utf-8")
    # Call the function with the required formatting argument.
    result = load_and_format_prompt(str(prompt_file), name="Alice")
    assert result == "Hello, Alice! This is a test prompt."
