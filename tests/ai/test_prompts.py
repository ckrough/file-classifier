"""Unit tests for the prompt_manager module."""

import pytest
from pathlib import Path
from unittest import mock

from src.ai.prompts import load_prompt_template, get_prompt_template
from langchain_core.prompts import ChatPromptTemplate


@pytest.mark.unit
def test_load_classification_prompt():
    """Test load_prompt_template returns ChatPromptTemplate for classification."""
    prompt_template = load_prompt_template("classification-agent")

    assert isinstance(prompt_template, ChatPromptTemplate)
    assert len(prompt_template.messages) == 2  # System + Human

    # Verify it has the expected input variables
    assert "filename" in prompt_template.input_variables
    assert "content" in prompt_template.input_variables


@pytest.mark.unit
def test_get_prompt_template_singleton():
    """Test that get_prompt_template caches prompts (singleton behavior)."""
    # Get the same prompt twice
    prompt1 = get_prompt_template("classification-agent")
    prompt2 = get_prompt_template("classification-agent")

    # Should be the exact same object (cached)
    assert prompt1 is prompt2


@pytest.mark.unit
def test_load_standards_enforcement_prompt():
    """Test loading standards enforcement agent prompt."""
    prompt_template = load_prompt_template("standards-enforcement-agent")

    assert isinstance(prompt_template, ChatPromptTemplate)
    assert len(prompt_template.messages) == 2


@pytest.mark.unit
def test_load_path_construction_prompt():
    """Test loading path construction agent prompt."""
    prompt_template = load_prompt_template("path-construction-agent")

    assert isinstance(prompt_template, ChatPromptTemplate)
    assert len(prompt_template.messages) == 2


@pytest.mark.unit
def test_load_conflict_resolution_prompt():
    """Test loading conflict resolution agent prompt."""
    prompt_template = load_prompt_template("conflict-resolution-agent")

    assert isinstance(prompt_template, ChatPromptTemplate)
    assert len(prompt_template.messages) == 2


@pytest.mark.unit
def test_load_prompt_template_missing_file():
    """Test that load_prompt_template raises FileNotFoundError if files are missing."""
    with mock.patch("src.ai.prompts.PROMPTS_DIR", Path("/nonexistent")):
        with pytest.raises(FileNotFoundError):
            load_prompt_template("classification-agent")


@pytest.mark.unit
def test_prompt_template_formats_correctly():
    """Test that the prompt template formats with actual values."""
    prompt_template = load_prompt_template("classification-agent")

    # Format with sample values
    messages = prompt_template.format_messages(
        filename="test.pdf", content="Sample content"
    )

    assert len(messages) == 2
    assert "test.pdf" in messages[1].content
    assert "Sample content" in messages[1].content
