"""Unit tests for the prompt_manager module."""

import pytest
from pathlib import Path
from unittest import mock

from src.ai_file_classifier.prompt_manager import (
    load_file_analysis_prompt,
    get_file_analysis_prompt,
    PROMPTS_DIR
)
from langchain_core.prompts import ChatPromptTemplate


def test_load_file_analysis_prompt():
    """Test that load_file_analysis_prompt returns a valid ChatPromptTemplate."""
    prompt_template = load_file_analysis_prompt()

    assert isinstance(prompt_template, ChatPromptTemplate)
    assert len(prompt_template.messages) == 2  # System + Human

    # Verify it has the expected input variables
    assert "filename" in prompt_template.input_variables
    assert "content" in prompt_template.input_variables


def test_get_file_analysis_prompt_singleton():
    """Test that get_file_analysis_prompt returns the same instance (singleton)."""
    # Clear the singleton
    import src.ai_file_classifier.prompt_manager as pm
    pm._file_analysis_prompt = None

    prompt1 = get_file_analysis_prompt()
    prompt2 = get_file_analysis_prompt()

    # Should be the exact same object
    assert prompt1 is prompt2


def test_load_file_analysis_prompt_missing_file():
    """Test that load_file_analysis_prompt raises FileNotFoundError if files are missing."""
    with mock.patch('src.ai_file_classifier.prompt_manager.PROMPTS_DIR', Path("/nonexistent")):
        with pytest.raises(FileNotFoundError):
            load_file_analysis_prompt()


def test_prompt_template_formats_correctly():
    """Test that the prompt template formats with actual values."""
    prompt_template = load_file_analysis_prompt()

    # Format with sample values
    messages = prompt_template.format_messages(
        filename="test.pdf",
        content="Sample content"
    )

    assert len(messages) == 2
    assert "test.pdf" in messages[1].content
    assert "Sample content" in messages[1].content
