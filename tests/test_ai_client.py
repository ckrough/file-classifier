"""Unit tests for the AIClient implementations."""

import json
from unittest.mock import patch, MagicMock

import pytest
from openai import OpenAIError

from src.ai_file_classifier.ai_client import OpenAIClient


@patch("src.config.logging_config.os.getenv")
@patch("src.ai_file_classifier.ai_client.os.getenv")
def test_openai_client_init_no_api_key(mock_ai_getenv, mock_logging_getenv):
    """
    Test that OpenAIClient raises a ValueError when the OPENAI_API_KEY environment variable is not set.
    """
    def ai_side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return None
        return default

    def logging_side_effect(key, default=None):
        if key == "DEBUG_MODE":
            return "false"
        return default

    mock_ai_getenv.side_effect = ai_side_effect
    mock_logging_getenv.side_effect = logging_side_effect
    mock_logging_getenv.side_effect = logging_side_effect
    with pytest.raises(ValueError) as excinfo:
        OpenAIClient()
    assert "OPENAI_API_KEY must be provided." in str(excinfo.value)


@patch("src.config.logging_config.os.getenv")
@patch("src.ai_file_classifier.ai_client.os.getenv")
def test_openai_client_init_success(mock_ai_getenv, mock_logging_getenv):
    """
    Test that OpenAIClient initializes successfully when the OPENAI_API_KEY environment variable is set.
    """
    def ai_side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "test_api_key"
        return default

    def logging_side_effect(key, default=None):
        if key == "DEBUG_MODE":
            return "false"
        return default

    mock_ai_getenv.side_effect = ai_side_effect
    mock_logging_getenv.side_effect = logging_side_effect
    client = OpenAIClient(api_key="test_api_key")
    assert client is not None


@patch("openai.resources.chat.Completions.create")
def test_analyze_content_success(mock_create):
    """
    Test that analyze_content successfully returns an Analysis object with correct data.
    """
    mock_response = MagicMock()
    # Create a mock message with 'content' as a JSON string
    mock_message = MagicMock()
    mock_message.content = json.dumps({
        "category": "Document",
        "vendor": "OpenAI",
        "description": "An analysis of the document content.",
        "date": "2023-10-01"
    })

    # Ensure that accessing message["content"] returns the same JSON string
    mock_message.__getitem__.return_value = mock_message.content

    # Assign the mock message to choices
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_create.return_value = mock_response

    client = OpenAIClient()
    analysis = client.analyze_content("system prompt", "user prompt", "model-name")
    mock_create.assert_called_once()
    assert analysis.category == "Document"
    assert analysis.vendor == "OpenAI"
    assert analysis.description == "An analysis of the document content."
    assert analysis.date == "2023-10-01"


@patch("openai.resources.chat.Completions.create", side_effect=OpenAIError("API Error"))
def test_analyze_content_exception(_mock_create):
    """Test that analyze_content raises RuntimeError when OpenAI API fails."""
    client = OpenAIClient()
    with pytest.raises(RuntimeError) as excinfo:
        client.analyze_content("system prompt", "user prompt", "model-name")
    assert "Error communicating with OpenAI API." in str(excinfo.value)
