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


# Security Tests - Path Traversal Protection


@pytest.mark.unit
def test_load_prompt_template_path_traversal_protection():
    """Test that path traversal attempts in prompt names are blocked."""
    malicious_names = [
        "../../../etc/passwd",
        "../../sensitive-data",
        "prompt/../../../attack",
        "../prompts/classification-agent",
        "subdir/../classification-agent",
    ]
    for name in malicious_names:
        with pytest.raises(ValueError) as exc:
            load_prompt_template(name)
        assert "Invalid prompt name" in str(exc.value)
        assert "path traversal" in str(exc.value).lower()


@pytest.mark.unit
def test_load_prompt_template_uppercase_rejected():
    """Test that uppercase prompt names are rejected."""
    invalid_names = [
        "Classification-Agent",
        "CLASSIFICATION-AGENT",
        "classification-Agent",
    ]
    for name in invalid_names:
        with pytest.raises(ValueError) as exc:
            load_prompt_template(name)
        assert "Invalid prompt name" in str(exc.value)
        assert "must match pattern" in str(exc.value)


@pytest.mark.unit
def test_load_prompt_template_special_chars_rejected():
    """Test that prompt names with invalid special characters are rejected."""
    invalid_names = [
        "classification agent",  # Spaces
        "classification/agent",  # Forward slash
        "classification\\agent",  # Backslash
        "classification@agent",  # Special char
        "classification;agent",  # Semicolon
        "classification&agent",  # Ampersand
    ]
    for name in invalid_names:
        with pytest.raises(ValueError) as exc:
            load_prompt_template(name)
        assert "Invalid prompt name" in str(exc.value)


@pytest.mark.unit
def test_load_prompt_template_valid_names():
    """Test that valid prompt names are accepted."""
    # These are actual valid prompts that exist (2-agent pipeline)
    # Note: path-construction and conflict-resolution agents removed
    valid_names = [
        "classification-agent",
        "standards-enforcement-agent",
    ]
    for name in valid_names:
        # Should not raise ValueError
        prompt = load_prompt_template(name)
        assert isinstance(prompt, ChatPromptTemplate)
