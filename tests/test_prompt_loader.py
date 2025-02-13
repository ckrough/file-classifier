"""
This module contains unit tests for the prompt_loader module.
"""

from pathlib import Path
import pytest
from src.ai_file_classifier.prompt_loader import load_and_format_prompt


def test_load_prompt_valid(tmp_path):
    """Test loading and formatting a prompt with valid arguments."""
    # Create a temporary prompt file with proper formatting.
    prompt_file: Path = tmp_path / "prompt.txt"
    prompt_file.write_text("Hello, {name}! This is a test prompt.", encoding="utf-8")
    # Call the function with the required formatting argument.
    result = load_and_format_prompt(str(prompt_file), name="Alice")
    assert result == "Hello, Alice! This is a test prompt."


def test_load_prompt_missing_keyword(tmp_path, caplog):
    """Test handling of missing required format keyword argument."""
    # Create a prompt file that requires a keyword argument.
    prompt_file: Path = tmp_path / "prompt.txt"
    prompt_file.write_text("Hello, {name}! This is a test prompt.", encoding="utf-8")
    # Call the function without providing the required 'name' keyword.
    result = load_and_format_prompt(str(prompt_file))
    assert result == ""
    # Verify that an error log was generated.
    assert any("Unexpected error loading or formatting prompt" in record.message
              for record in caplog.records)


def test_load_prompt_permission_error(monkeypatch, tmp_path, caplog):
    """Test handling of permission errors when reading prompt file."""
    # Patch open to simulate a PermissionError.
    def fake_open(*args, **kwargs):
        raise PermissionError("Fake permission error")
    monkeypatch.setattr("builtins.open", fake_open)
    prompt_file: Path = tmp_path / "prompt.txt"
    prompt_file.write_text("Hello, {name}!", encoding="utf-8")
    # Call the function; it should handle the PermissionError and return an empty string.
    result = load_and_format_prompt(str(prompt_file), name="Alice")
    assert result == ""
    # Confirm that the appropriate error log message is present.
    assert any("Permission denied when accessing prompt file" in record.message
              for record in caplog.records)
